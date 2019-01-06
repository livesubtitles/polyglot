import math
import os
import re
import codecs
import matplotlib.pyplot as plt

COST_GOOGLE_SPEECH_API_15_SECONDS = 0.006
GOOGLE_MONTHLY_LIMIT_SECONDS = 60000000
COST_GOOGLE_TRANSLATE_API_PER_CHAR = 20.0 / 1000000.0

videos_english = "subtitles/english"

def get_length(hours, minutes):
    return (hours * 60 + minutes) * 60

def speech_recognition_price(duration_seconds):
    #round up
    duration_seconds = math.ceil(duration_seconds / 15.0)
    # up to 1,000,000 minutes, i.e. 16,666 hours, 694 days of speech per month
    return COST_GOOGLE_SPEECH_API_15_SECONDS * duration_seconds

def translation_price(num_characters):
    # limit of a billion characters per month
    return COST_GOOGLE_TRANSLATE_API_PER_CHAR * num_characters

def calculate_price_video(video_seconds, subtitle_number_chars):
    return speech_recognition_price(video_seconds) + translation_price(subtitle_number_chars)

def calculate_num_chars(path):
    with codecs.open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    # for srt files coming from Windows
    content = content.replace("\r", "").replace("\t", "")
    lines = content.split("\n")
    sections = []
    sec = []
    for line in lines:
        if line == "":
            sections.append(sec)
            sec = []
            continue
        sec.append(line)
    sections = [x for x in sections if len(x) > 2]
    # grab last subtitle time and use it as duration of movie
    last_section_time = sections[-1][1]
    m = re.match(r"(.*) --> (?P<end_time>.*)", last_section_time)
    end_time = m.groupdict()["end_time"]
    hours_minutes = end_time.split(":")
    hours = int(hours_minutes[0])
    minutes = int(hours_minutes[1])
    time = (hours, minutes)
    for idx in range(len(sections)):
        sections[idx] = sections[idx][2:]

    value = 0
    for s in sections:
        for sentence in s:
            value += len(sentence)

    print("{} characters".format(value))
    return value, time

def to_hour_from_seconds(seconds):
    return seconds / 3600.0

def run_analysis(subtitle_dir):
    results_per_language = {}
    # expects a directory with directories (languages), each with .srt files
    for root, dirs, files in os.walk(subtitle_dir):
        if root == subtitle_dir:
            continue
        print(root)
        language = root.split("/")[1]
        print("**********************")
        print(language)
        results = []
        for file in files:
            print("")
            path = "{}/{}".format(root, file)
            chars, time = calculate_num_chars(path)
            seconds = get_length(time[0], time[1])
            price = calculate_price_video(seconds, chars)
            r = (seconds, price, price / to_hour_from_seconds(seconds), file, chars)
            results.append(r)
            print("{}, time: {} with price: USD {} in {}".format(file.split(".")[0], seconds, price, language))
            print("Price per user per hour: {}".format(r[2]))
        print("***********************")
        # save results
        results_per_language[language] = sorted(results, key=lambda x: x[3])
    return results_per_language

def get_avg(res):
    value = 0
    for r in res:
        value += r[2]
    return value / len(res)

def get_avg_price_overall(rs):
    count = 0
    value = 0
    for key in rs:
        for v in rs[key]:
            value += v[2]
            count += 1
    return value / count

def avg_price_per_language(results):
    return { lang: get_avg(results[lang]) for lang in results }

def get_avg_number_chars_per_hour_total(rspl):
    resdict = {}
    chars = 0
    t = 0
    for lang in rspl:
        resdict[lang] = []
        r = rspl[lang]
        for p in r:
            chars = p[4]
            t = p[0]
            resdict[lang].append((p[3], chars / to_hour_from_seconds(t)))
    return resdict


def plot_price_per_hour(rs):
    # plot of price per hour for each subtitle file per language
    values = [list(map(lambda x: x[2], rs[key])) for key in rs]
    srt_names = [list(map(lambda x: x[3], rs[key])) for key in rs][0]
    avg_price_dict = avg_price_per_language(rs)
    languages = [key for key in rs]
    avg_price_overall = get_avg_price_overall(rs)
    label_idx = 0
    print(avg_price_overall)
    for v in values:
        label = languages[label_idx]
        srts = ["SRT " + str(i) for i in range(1, len(v) + 1)]
        plt.plot(srts, v, label=label, marker="o")
        label_idx += 1
    plt.axhline(y=avg_price_overall, linestyle='dashed', color="black", label="Avg price")
    plt.legend(loc="upper left")
    plt.ylabel("USD per user per hour")
    plt.xlabel("Subtitle files")
    plt.title("Average price per user per hour in different languages")
    plt.show()

def plot_characters_per_hour(cs_per_hour):
    list_gen = (cs_per_hour[key] for key in cs_per_hour)
    chars = map(lambda x: [p[1] for p in x], list_gen)
    avg = sum(list(map(sum, chars))) / 15.0
    print(avg)
    values = [list(map(lambda x: x[1], cs_per_hour[key])) for key in cs_per_hour]
    languages = [key for key in cs_per_hour]
    label_idx = 0
    for v in values:
        srts = ["SRT " + str(i) for i in range(1, len(v) + 1)]
        label = languages[label_idx]
        plt.plot(srts, v, label=label, marker="o")
        label_idx += 1
    plt.axhline(y=avg, linestyle='dashed', color="black", label="Avg number of characters")
    plt.legend(loc="upper left")
    plt.ylabel("# characters per hour")
    plt.xlabel("Subtitle files")
    plt.title("Number of characters per hour in subtitles in different languages")
    plt.show()


rs = run_analysis("subtitles")
cs_per_hour = get_avg_number_chars_per_hour_total(rs)
plot_characters_per_hour(cs_per_hour)
#plot_price_per_hour(rs)
