import requests
from bs4 import BeautifulSoup
import json
import time

# !import re  # For looking for eventual word counts in job posts & controlling the validity of url input.


# TODO: Add to json: user agent, username, password
# Regarding password: "<Akuli> the only thing that comes to mind is first logging
# in with browser, then sending the exact same headers (User-Agent and friends)
# and cookies with request"
def read_from_json():
    """ Reads all the job posts from job_posts.json """
    try:
        with open("job_posts.json", "r") as job_posts_json:
            json_content = json.load(job_posts_json)
            return json_content
    except FileNotFoundError:
        json_content = {
            "Requests URL": None,
            "DBMR": False,
            "Fixed Lowest Rate": 0,
            "Hourly Lowest Rate": 0,
            "Job Posts": None,
        }
        return json_content


def write_to_json(json_content):
    """ Writes the latest web scrape and UserInput data to job_posts.json """
    json_dict = {
        "Requests URL": json_content["Requests URL"],
        "DBMR": json_content["DBMR"],
        "Fixed Lowest Rate": json_content["Fixed Lowest Rate"],
        "Hourly Lowest Rate": json_content["Hourly Lowest Rate"],
        "Job Posts": json_content["Job Posts"],
    }
    with open("job_posts.json", "w") as json_dump:
        json.dump(json_dict, json_dump, indent=4)


def extract_hourly_price(hourly_payment_type):
    """ Returns the hourly payment as int for message_printer() if-statement """
    if "-" in hourly_payment_type:
        # Accounts for job_post["Payment Type"] == "Hourly: $X.00–$Y.00"
        # Looking at the $Y to account for the payment range.
        return int(float(hourly_payment_type.split()[1].split("-")[1].lstrip("$")))
    else:
        # Accounts for job_post["Payment Type"] == "Hourly: $X.00"
        return int(float(hourly_payment_type.split()[1].lstrip("$")))


def extract_fixed_price(fixed_payment_type):
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


def message_printer(json_content, new_job_posts):
    """ Prints number of new jobs (that satisfy user budget criteria) & their details """

    fixed_lowest_rate = json_content["Fixed Lowest Rate"]

    hourly_lowest_rate = json_content["Hourly Lowest Rate"]

    selected_new_job_posts = []

    for job_post in new_job_posts:
        # print(job_post)  # Use this line to debug what job post might cause an error. Keep for future debugging as well

        # job_post["Payment Type"] can be "Fixed-price", "Hourly: $X.00–$Y.00", or "Hourly"
        if (
            job_post["Payment Type"] == "Fixed-price"
            and extract_fixed_price(job_post["Budget"]) >= fixed_lowest_rate
        ):
            selected_new_job_posts.append(job_post)
        elif (
            job_post["Payment Type"].split()[0] == "Hourly:"
            and extract_hourly_price(job_post["Payment Type"]) >= hourly_lowest_rate
        ) or job_post["Payment Type"] == "Hourly":
            selected_new_job_posts.append(job_post)

    if len(selected_new_job_posts) == 0:
        print("No New Job Posts")  # TODO: Remove this and exhange for return
    elif len(selected_new_job_posts) == 1:
        print(
            """There is 1 new job post.
        """
        )
    else:
        print(
            f"""There are {len(selected_new_job_posts)} new job posts.
        """
        )

    if len(selected_new_job_posts) >= 4:
        for job_post in selected_new_job_posts:
            if job_post["Payment Type"] == "Fixed-price":
                print(
                    f"{job_post['Job Title']} – {job_post['Payment Type']}: {job_post['Budget']}"
                )
            else:
                print(f"{job_post['Job Title']} – {job_post['Payment Type']}")
            print(job_post["Job Post URL"] + "\n")
    else:
        for job_post in selected_new_job_posts:
            print(job_post["Job Title"])
            if job_post["Payment Type"] == "Fixed-price":
                print(job_post["Payment Type"] + " " + job_post["Budget"])
            else:
                print(job_post["Payment Type"])
            print(job_post["Job Description"] + "...")
            print(job_post["Job Post URL"] + "\n")


def json_difference_checker(json_content, job_post_list):
    """Controls where in the new webscrape the highest job post in json is,
    to check amount of new posts"""

    old_job_urls = [job_post["Job Post URL"] for job_post in json_content["Job Posts"]]

    new_job_posts = [
        job_post
        for job_post in job_post_list
        if job_post["Job Post URL"] not in old_job_urls
    ]

    message_printer(json_content, new_job_posts)

    json_content["Job Posts"] = job_post_list


def job_post_scraper(json_content):
    """ Scrapes Upwork for job posts and stores details in variables """
    # TODO: Control that input is valid upwork search link. (Regex library)
    # TODO: Tell the user if there is no URL specified when trying to do request

    # Translation URL for testing: https://www.upwork.com/ab/jobs/search/?page=2&q=(translat%20OR%20proofread)%20AND%20swedish&sort=recency

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
        except requests.exceptions.HTTPError as errh:
            print("HTTP Error:", errh)
            print("Please try a different URL")
            return
        except requests.exceptions.ConnectionError:
            print("Error Connecting")
            print("Please check you internet connection and try again.")
            return
        except requests.exceptions.Timeout:
            print("Your request timed out.")
            if connection_attempts == 3:
                return
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
        else:
            job_budget = ""

        job_description = job_post.find("span", class_="js-description-text").text[:150]

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

    json_difference_checker(json_content, job_post_list)


def scrape_loop(json_content):
    while json_content["Requests URL"] is None:
        time.sleep(0.5)  # wait for url to be entered
    sleep_time = 30  # TODO: json_content["Sleep Time"] * 60
    while True:
        print("Calling job_post_scraper")
        job_post_scraper(json_content)
        print("Scraper has run. Time to sleep!")
        time.sleep(sleep_time)
        print("Waking up, back to business!")
