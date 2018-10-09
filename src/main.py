#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

import time
import urllib.request
import speech_recognition as sr

import os

# TODO: remove this hack
def recognize_sphinx(audio_data, language="en-US", keyword_entries=None, grammar=None, show_all=False):
    """
    Performs speech recognition on ``audio_data`` (an ``AudioData`` instance), using CMU Sphinx.
    The recognition language is determined by ``language``, an RFC5646 language tag like ``"en-US"`` or ``"en-GB"``, defaulting to US English. Out of the box, only ``en-US`` is supported. See `Notes on using `PocketSphinx <https://github.com/Uberi/speech_recognition/blob/master/reference/pocketsphinx.rst>`__ for information about installing other languages. This document is also included under ``reference/pocketsphinx.rst``. The ``language`` parameter can also be a tuple of filesystem paths, of the form ``(acoustic_parameters_directory, language_model_file, phoneme_dictionary_file)`` - this allows you to load arbitrary Sphinx models.
    If specified, the keywords to search for are determined by ``keyword_entries``, an iterable of tuples of the form ``(keyword, sensitivity)``, where ``keyword`` is a phrase, and ``sensitivity`` is how sensitive to this phrase the recognizer should be, on a scale of 0 (very insensitive, more false negatives) to 1 (very sensitive, more false positives) inclusive. If not specified or ``None``, no keywords are used and Sphinx will simply transcribe whatever words it recognizes. Specifying ``keyword_entries`` is more accurate than just looking for those same keywords in non-keyword-based transcriptions, because Sphinx knows specifically what sounds to look for.
    Sphinx can also handle FSG or JSGF grammars. The parameter ``grammar`` expects a path to the grammar file. Note that if a JSGF grammar is passed, an FSG grammar will be created at the same location to speed up execution in the next run. If ``keyword_entries`` are passed, content of ``grammar`` will be ignored.
    Returns the most likely transcription if ``show_all`` is false (the default). Otherwise, returns the Sphinx ``pocketsphinx.pocketsphinx.Decoder`` object resulting from the recognition.
    Raises a ``speech_recognition.UnknownValueError`` exception if the speech is unintelligible. Raises a ``speech_recognition.RuntimeError`` exception if there are any issues with the Sphinx installation.
    """
    assert isinstance(audio_data, sr.AudioData), "``audio_data`` must be audio data"
    assert isinstance(language, str) or (isinstance(language, tuple) and len(language) == 3), "``language`` must be a string or 3-tuple of Sphinx data file paths of the form ``(acoustic_parameters, language_model, phoneme_dictionary)``"
    assert keyword_entries is None or all(isinstance(keyword, (type(""), type(u""))) and 0 <= sensitivity <= 1 for keyword, sensitivity in keyword_entries), "``keyword_entries`` must be ``None`` or a list of pairs of strings and numbers between 0 and 1"

    # import the PocketSphinx speech recognition module
    try:
        from pocketsphinx import pocketsphinx, Jsgf, FsgModel

    except ImportError:
        raise RuntimeError("missing PocketSphinx module: ensure that PocketSphinx is set up correctly.")
    except ValueError:
        raise RuntimeError("bad PocketSphinx installation; try reinstalling PocketSphinx version 0.0.9 or better.")
    if not hasattr(pocketsphinx, "Decoder") or not hasattr(pocketsphinx.Decoder, "default_config"):
        raise RuntimeError("outdated PocketSphinx installation; ensure you have PocketSphinx version 0.0.9 or better.")

    if isinstance(language, str):  # directory containing language data
        # hack the library to make file path correct
        # TODO: remove the hack?
        language_directory = os.path.join(os.path.dirname(os.path.realpath('/Users/zwang541/Library/Python/3.7/lib/python/site-packages/speech_recognition/__init__.py')), "pocketsphinx-data", language)
        if not os.path.isdir(language_directory):
            raise RuntimeError("missing PocketSphinx language data directory: \"{}\"".format(language_directory))
        acoustic_parameters_directory = os.path.join(language_directory, "acoustic-model")
        language_model_file = os.path.join(language_directory, "language-model.lm.bin")
        phoneme_dictionary_file = os.path.join(language_directory, "pronounciation-dictionary.dict")
    else:  # 3-tuple of Sphinx data file paths
        acoustic_parameters_directory, language_model_file, phoneme_dictionary_file = language
    if not os.path.isdir(acoustic_parameters_directory):
        raise RuntimeError("missing PocketSphinx language model parameters directory: \"{}\"".format(acoustic_parameters_directory))
    if not os.path.isfile(language_model_file):
        raise RuntimeError("missing PocketSphinx language model file: \"{}\"".format(language_model_file))
    if not os.path.isfile(phoneme_dictionary_file):
        raise RuntimeError("missing PocketSphinx phoneme dictionary file: \"{}\"".format(phoneme_dictionary_file))

    # create decoder object
    config = pocketsphinx.Decoder.default_config()
    config.set_string("-hmm", acoustic_parameters_directory)  # set the path of the hidden Markov model (HMM) parameter files
    config.set_string("-lm", language_model_file)
    config.set_string("-dict", phoneme_dictionary_file)
    config.set_string("-logfn", os.devnull)  # disable logging (logging causes unwanted output in terminal)
    config.set_float("-beam", 1e-100)
    config.set_float("-wbeam", 1e-80)
    # config.set_int("-ds", 3)

    decoder = pocketsphinx.Decoder(config)

    # obtain audio data
    raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)  # the included language models require audio to be 16-bit mono 16 kHz in little-endian format

    # obtain recognition results
    if keyword_entries is not None:  # explicitly specified set of keywords
        with PortableNamedTemporaryFile("w") as f:
            # generate a keywords file - Sphinx documentation recommendeds sensitivities between 1e-50 and 1e-5
            f.writelines("{} /1e{}/\n".format(keyword, 100 * sensitivity - 110) for keyword, sensitivity in keyword_entries)
            f.flush()

            # perform the speech recognition with the keywords file (this is inside the context manager so the file isn;t deleted until we're done)
            decoder.set_kws("keywords", f.name)
            decoder.set_search("keywords")
            decoder.start_utt()  # begin utterance processing
            decoder.process_raw(raw_data, False, True)  # process audio data with recognition enabled (no_search = False), as a full utterance (full_utt = True)
            decoder.end_utt()  # stop utterance processing
    elif grammar is not None:  # a path to a FSG or JSGF grammar
        if not os.path.exists(grammar):
            raise ValueError("Grammar '{0}' does not exist.".format(grammar))
        grammar_path = os.path.abspath(os.path.dirname(grammar))
        grammar_name = os.path.splitext(os.path.basename(grammar))[0]
        fsg_path = "{0}/{1}.fsg".format(grammar_path, grammar_name)

        jsgf = Jsgf(grammar)
        # hack the library to correct jsgf rule name
        # TODO: remove the hack?
        rule = jsgf.get_rule("captcha.string")
        fsg = jsgf.build_fsg(rule, decoder.get_logmath(), 7.5)
        fsg.writefile(fsg_path)

        decoder.set_fsg(grammar_name, fsg)
        decoder.set_search(grammar_name)
        decoder.start_utt()
        decoder.process_raw(raw_data, False, True)  # process audio data with recognition enabled (no_search = False), as a full utterance (full_utt = True)
        decoder.end_utt()  # stop utterance processing
    else:  # no keywords, perform freeform recognition
        decoder.start_utt()  # begin utterance processing
        decoder.process_raw(raw_data, False, True)  # process audio data with recognition enabled (no_search = False), as a full utterance (full_utt = True)
        decoder.end_utt()  # stop utterance processing

    if show_all: return decoder

    # return results
    hypothesis = decoder.hyp()
    if hypothesis is not None: return hypothesis.hypstr
    raise UnknownValueError()  # no transcriptions available

class Query():
    url = 'https://ceac.state.gov/CEACStatTracker/Status.aspx'
    visa_type_elem_name = 'ctl00$ContentPlaceHolder1$Visa_Application_Type'
    location_select_elem_name = 'ctl00$ContentPlaceHolder1$Location_Dropdown'
    ds160_textbox_elem_name = 'ctl00$ContentPlaceHolder1$Visa_Case_Number'
    submit_elem_id = 'ctl00_ContentPlaceHolder1_btnSubmit'
    captcha_elem_id = 'c_status_ctl00_contentplaceholder1_defaultcaptcha_CaptchaImage'
    refresh_captcha_id = 'c_status_ctl00_contentplaceholder1_defaultcaptcha_ReloadIcon'
    sound_captcha_id = 'c_status_ctl00_contentplaceholder1_defaultcaptcha_SoundIcon'
    audio_element_id = 'LBD_CaptchaSoundAudio_c_status_ctl00_contentplaceholder1_defaultcaptcha'

    def __init__(self):
        return

    def send_query(self, visa_type, visa_location, ds160_number):
        driver = webdriver.Chrome()
        driver.get(Query.url)
        
        type_select = Select(driver.find_element_by_name(Query.visa_type_elem_name))
        type_select.select_by_visible_text(visa_type)
        if __debug__:
            time.sleep(1)

        location_select = Select(driver.find_element_by_name(Query.location_select_elem_name))
        location_select.select_by_visible_text(visa_location)
        if __debug__:
            time.sleep(1)

        ds160_textbox = driver.find_element_by_name(Query.ds160_textbox_elem_name)
        ds160_textbox.clear()
        ds160_textbox.send_keys(ds160_number)
        if __debug__:
            time.sleep(1)

        submit = driver.find_element_by_id(Query.submit_elem_id)
        # submit.click()

    def download_captcha_imgs(self, num):
        driver = webdriver.Chrome()
        driver.get(Query.url)

        file_prefix = str(int(time.time()))

        for cnt in range(num):
            captcha_img = driver.find_element_by_id(Query.captcha_elem_id)
            refresh_captcha_btn = driver.find_element_by_id(Query.refresh_captcha_id)
            captcha_src = captcha_img.get_attribute('src')
            urllib.request.urlretrieve(captcha_src, '../imgs/' + file_prefix + '_' + str(cnt))
            refresh_captcha_btn.click()
            time.sleep(1)
        return

    def download_captcha_audios(self, num):
        driver = webdriver.Chrome()
        driver.get(Query.url)

        file_prefix = str(int(time.time()))

        for cnt in range(num):
            play_captcha_btn = driver.find_element_by_id(Query.sound_captcha_id)
            play_captcha_btn.click()
            time.sleep(1)

            audio_element = driver.find_element_by_id(Query.audio_element_id)
            audio_url = audio_element.get_attribute('src')
            urllib.request.urlretrieve(audio_url, '../audios/' + file_prefix + '_' + str(cnt) + '.wav')

            time.sleep(5)
            refresh_captcha_btn = driver.find_element_by_id(Query.refresh_captcha_id)
            refresh_captcha_btn.click()
            time.sleep(1)
        return

    def audio_recognition(self, audio_file):
        audio_source = sr.AudioFile(audio_file)
        with audio_source as source:
            r = sr.Recognizer()
            audio = r.record(source)
            out = recognize_sphinx(audio, grammar = 'grammar.jsgf')
            print(out)

if __name__ == "__main__":
    visa_location = 'CHINA, BEIJING'
    ds160_number = 'xxxxxxxx'
    visa_type = 'NONIMMIGRANT VISA (NIV)'

    q = Query()
    # q.send_query(visa_type, visa_location, ds160_number)
    # q.download_captcha_audios(10)
    q.audio_recognition('../audios/1539081582_5.wav')