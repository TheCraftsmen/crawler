Web CRAWLER
===========

For run the project, first you need to create a virtualenv with python 3 version in the project root folder.

```
$ virtualenv venv --python=python3
```

after active this venv.

```
$ source venv/bin/activate
```

and with the venv activated install the lib in the requirements.txt.

```
(venv)$ pip install -r requirements.txt
```

the ouput file are going to generated inside the root folder.

by default the crawler make two requests per seconds.

in settings.py you can configure the urls that you want to crawl.

```
URLS = [
    {
        "domain": "debenhams.com",
        "website": "https://www.debenhams.com/"
    }
]
```

when you the configuration you can run the crawler with the next command.

```
$ python app.py
```

this program permit multi domain crawl
permite multiples el crawleo en multiples dominio.

for run each domain crawl, the program use the ProcessPoolExecutor for use in a better way the cpu.



You could improve the memory consumption of the process by rewriting the code to cython,
but even in the local test the memory consumption is quite moderate because I am not using multithreading.

The system has auto saved every 200 seconds.

Also this program respects the robots.txt rules to crawl;

You can activate a flag in the class to search for urls in the tag scripts, but it only corresponds in a few cases,
by default the flag is in False.

I decided to use the combo "requests" + "beatifulsoup4", because the development experience is very good
and this libs have a very good performance. Also the idea was to be able to show a bit of my development logic

For large-scale projects I would think about implementations
1) adding dask distributed or python ray with cython optimization to this project
2) using the scrapy framework