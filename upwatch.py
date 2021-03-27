from bs4 import BeautifulSoup  # type: ignore
from typing import TypedDict
import requests
import json
import time
import pathlib
from typing import Optional, List

# !import re  # For looking for eventual word counts in job posts & controlling the validity of url input.

JobPost = TypedDict(
    "JobPost",
    {
        "Job Title": str,
        "Payment Type": str,
        "Budget": str,
        "Job Description": str,
        "Job Post URL": str,
    },
)

JsonContent = TypedDict(
    "JsonContent",
    {
        "Requests URL": str,
        "Run on startup": bool,
        "Scrape interval": int,
        "DBMR": bool,
        "Fixed Lowest Rate": int,
        "Hourly Lowest Rate": int,
        "Ignore no budget": bool,
        "Job Posts": Optional[JobPost],
    },
)  # "Job Posts" can also be "None" . Does it matter?


# TODO: Add to json: user agent
def read_from_json(json_path: pathlib.Path) -> JsonContent:
    """ Reads all the job posts from job_posts.json """
    try:
        with open(json_path / "job_posts.json", "r") as job_posts_json:
            json_content = json.load(job_posts_json)
            json_found = True
            return json_content, json_found
    except FileNotFoundError:
        json_found = False
        json_content = {
            "Requests URL": "",
            "Run on startup": True,
            "Scrape interval": 10,
            "DBMR": False,
            "Fixed Lowest Rate": 0,
            "Hourly Lowest Rate": 0,
            "Ignore no budget": False,
            "Job Posts": None,
        }
        return json_content, json_found


def write_to_json(json_content: JsonContent, json_path: pathlib.Path) -> None:
    """ Writes the latest web scrape and UserInput data to job_posts.json """
    json_dict = {
        "Requests URL": json_content["Requests URL"],
        "Run on startup": json_content["Run on startup"],
        "Scrape interval": json_content["Scrape interval"],
        "DBMR": json_content["DBMR"],
        "Fixed Lowest Rate": json_content["Fixed Lowest Rate"],
        "Hourly Lowest Rate": json_content["Hourly Lowest Rate"],
        "Ignore no budget": json_content["Ignore no budget"],
        "Job Posts": json_content["Job Posts"],
    }
    with open(json_path / "job_posts.json", "w") as json_dump:
        json.dump(json_dict, json_dump, indent=4)


def extract_hourly_price(hourly_payment_type: str) -> int:
    """ Returns the hourly payment as int for message_printer() if-statement """
    if "-" in hourly_payment_type:
        # Accounts for job_post["Payment Type"] == "Hourly: $X.00–$Y.00"
        # Looking at the $Y to account for the payment range.
        return int(float(hourly_payment_type.split()[1].split("-")[1].lstrip("$")))
    else:
        # Accounts for job_post["Payment Type"] == "Hourly: $X.00"
        return int(float(hourly_payment_type.split()[1].lstrip("$")))


def extract_fixed_price(fixed_payment_type: str) -> int:
    """ Returns the fixed price as int for message_printer() if-statement """
    # Accounts for job_post["Budget"] == "$1,234"
    if "," in fixed_payment_type:
        return int((fixed_payment_type).replace(",", "").lstrip("$"))
    # Accounts for job_post["Budget"] == "$XK" or "$X.YK"
    elif "K" in fixed_payment_type:
        if "." in fixed_payment_type:
            return int((float(fixed_payment_type.lstrip("$").rstrip("K"))) * 1000)
        else:
            return int(fixed_payment_type.lstrip("$").rstrip("K")) * 1000
    # Accounts for job_post["Budget"] == "$X"
    else:
        return int(fixed_payment_type.lstrip("$"))


def json_difference_checker(
    json_content: JsonContent, job_post_list: List[JobPost]
) -> List[JobPost]:
    """Checks the difference between current scrape and job posts
    stored in json to print any new job posts"""

    old_job_urls = [job_post["Job Post URL"] for job_post in json_content["Job Posts"]]

    new_job_posts = [
        job_post
        for job_post in job_post_list
        if job_post["Job Post URL"] not in old_job_urls
    ]

    json_content["Job Posts"] = job_post_list

    return new_job_posts


def job_post_scraper(json_content: JsonContent) -> List[JobPost]:
    """ Scrapes Upwork for job posts and stores details in variables """
    # TODO: Control that input is valid upwork search link. (Regex library)
    # TODO: Tell the user if there is no URL specified when trying to do request

    # Translation URL for testing: https://www.upwork.com/ab/jobs/search/?from_recent_search=true&q=(translat%20OR%20proofread)%20AND%20swedish&sort=recency
    # Logo URL for testing: https://www.upwork.com/ab/jobs/search/?q=logo&sort=recency

    url = json_content["Requests URL"]

    #       File "/Users/Writing/Documents/Python/Upwatch/env/lib/python3.9/site-packages/requests/models.py", line 390, in prepare_url
    #     raise MissingSchema(error)
    # requests.exceptions.MissingSchema: Invalid URL 'Set URL': No schema supplied. Perhaps you meant http://Set URL?

    connection_attempts = 1

    while True:
        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
                },
                timeout=3,
            )  # TODO: Figure out how to fetch User Agent on current system.
            response.raise_for_status()
            break
        # except requests.exceptions.HTTPError as errh:  # TODO Error messages need to be communicated to user in a different way.
        #     print("HTTP Error:", errh)
        #     print("Please try a different URL")
        #     return
        # except requests.exceptions.ConnectionError:
        #     print("Error Connecting")
        #     print("Please check you internet connection and try again.")
        #     return
        except requests.exceptions.Timeout:
            print("Your request timed out.")
            if connection_attempts == 3:
                raise NotImplementedError
            time.sleep(30)
            print("Trying again...")
            connection_attempts += 1

    soup = BeautifulSoup(response.text, "lxml")

    job_posts = soup.find_all("section", class_="air-card-hover")

    job_post_list = []

    for job_post in job_posts[:-1]:

        job_title = job_post.find("up-c-line-clamp").text

        job_payment_type = job_post.find("strong", class_="js-type").text.strip()

        if job_payment_type == "Fixed-price":
            job_budget = job_post.find("strong", class_="js-budget").text.strip()
        # elif job_payment_type.startswith("Hourly:"):
        #     job_budget = job_payment_type.split()[1]  # TODO: Implement this and simplify extract_hourly_price
        else:
            job_budget = ""

        job_description = job_post.find("span", class_="js-description-text").text

        job_post_url = job_post.find("a", class_="job-title-link").attrs["href"]

        job_post_dict = {
            "Job Title": job_title,
            "Payment Type": job_payment_type,
            "Budget": job_budget,
            "Job Description": job_description,
            "Job Post URL": "https://upwork.com" + job_post_url,
        }

        job_post_list.append(job_post_dict)

    if json_content["Job Posts"] is None:
        json_content["Job Posts"] = job_post_list

    return json_difference_checker(json_content, job_post_list)
