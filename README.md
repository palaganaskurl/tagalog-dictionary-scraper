# tagalog-dictionary-scraper
Scraper for [https://tagalog.pinoydictionary.com](https://tagalog.pinoydictionary.com)

## How To Run
Create virtualenv or whatever your environment is
```
pip install -r requirements.txt
```

```
python src/tagalog_dictionary_scraper.py
```

## Words
Words scraped are inside the words folder.

## Issues
Some words have weird formatting

Example: (niyayakap, niyakap, yayakapin) v., inf. 1. embrace to show love; 2. clasp to the breast; 3. espouse fig.

Some parts of speech are located on weird locations in the definition.

Some punctuation marks are not removed in the definition.

Some parts of speech are added to certain words even if that word doesn't contain the part of speech because ```.find() ```. I can't think of any intelligent way to guess the part of speech.

And many more...

Originally, the plan was to render the JavaScript of every page to extract the parts of speech properly but my machine can't handle the rendering of too many pages quickly. Though, the use of rendering is feasible, I don't want to wait long for so long to render each page then parse the contents.
 

## License
[MIT](https://choosealicense.com/licenses/mit/)