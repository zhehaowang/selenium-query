#!/usr/bin/env python3

from pydub import AudioSegment
from pydub.silence import split_on_silence

import glob

class Split():
    def __init__(self):
        return

    def match_target_amplitude(self, aChunk, target_dBFS):
        ''' Normalize given audio chunk '''
        change_in_dBFS = target_dBFS - aChunk.dBFS
        return aChunk.apply_gain(change_in_dBFS)

    def split_and_export(self, afile, min_silence_len = -32, silence_thresh = 350, length_threshold = 100):
        song = AudioSegment.from_wav(afile)
        file_name = afile.split('.')[-2].split('/')[-1]

        length_threshold = 100

        chunks = split_on_silence(song,
            min_silence_len=350,

            # consider it silent if quieter than -32 dBFS
            silence_thresh=-32
        )
        log = ""
        #Process each chunk per requirements
        for i, chunk in enumerate(chunks):
            log += str(i) + ' : ' + str(len(chunk))
            if len(chunk) < length_threshold:
                print('skipped segment ' + str(i) + ' length ' + str(len(chunk)))
                log += ' (skipped)'
                continue

            #Create 0.1 seconds silence chunk
            silence_chunk = AudioSegment.silent(duration = 50)

            #Add 0.5 sec silence to beginning and end of audio chunk
            audio_chunk = silence_chunk + chunk + silence_chunk

            #Normalize each audio chunk
            normalized_chunk = self.match_target_amplitude(audio_chunk, -20.0)

            #Export audio chunk with new bitrate
            print("exporting {0}_{1}.wav".format(file_name, i) )
            normalized_chunk.export("../audios/split/{0}_{1}.wav".format(file_name, i), format="wav")
            log += '\n'

        with open("../audios/split/{0}.txt".format(file_name), 'w') as log_file:
            log_file.write(log)
            print("writing log")

if __name__ == "__main__":
    split = Split()
    for afile in glob.glob("../audios/*.wav"):
        split.split_and_export(afile)
