# Research

### Captcha

It appears all the captcha for the future timestamps are generated with a get request to the following url, e.g., with the link below (note the timestamp get param 'd'), and randomized

https://ceac.state.gov/CEACStatTracker/BotDetectCaptcha.ashx?get=image&c=c_status_ctl00_contentplaceholder1_defaultcaptcha&t=03d1eb5bdaf6498c8ad69e483e53d711&d=2049044050098

Correspondingly, an audio can be downloaded via links like this one

https://ceac.state.gov/CEACStatTracker/BotDetectCaptcha.ashx?get=sound&c=c_status_ctl00_contentplaceholder1_defaultcaptcha&t=87919b2027084ba28214645ae8661bc4&s=kc2ijlCWEDh%2fhWS8tfji%2bGAZCKkpmlB5KN51CbQsS76ygPDZdgu5%2byhf7%2fuf52HLXNtNR9wx0Iw%3d&d=1539044885437&e=1

(grabbed via breakpoint in Chrome console)

##### Image approach

Tensorflow CNN?

Labeling?

##### Sound approach

Alphanumeric only: PocketSphinx with custom JSGF grammar, pretty abysmal accuracy without fine tuning.

Split by onset then recognize?