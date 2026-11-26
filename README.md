![make.fun](https://make.fun/badge/news-image-20261126.svg)
![Rank](https://make.fun/badge/news-image-20261126/Arifpratama19/news-image-20261126/rank.svg)
![Reward](https://make.fun/badge/news-image-20261126/Arifpratama19/news-image-20261126/reward.svg)

# The World Today — Thursday, 26 November 2026

[make.fun bounty: Sum up 26 November's world news in one image](https://make.fun/bounty/news-image-20261126)

A newspaper front-page poster summing up Thursday 26 November 2026 in one
image: 30+ dated stories from 9 regions, with illustrated hero scenes.
Every story is drawn by hand in code — text from a small bitmap font defined
in the file, illustrations from basic shapes — and the PNG bytes are written
by hand with zlib and struct.

## Run it

```sh
python3 main.py            # writes /output/entry.png
python3 main.py out.png    # or pass an output path
OUTPUT_PATH=out.png python3 main.py
```

Pure Python 3 standard library, no network, no files read at runtime.
Running it twice produces byte-identical output.
