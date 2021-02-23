import requests
from bs4 import BeautifulSoup
import json
import time

# !import re  # For looking for eventual word counts in job posts & controlling the validity of url input.

# TODO: Program needs to log into Upwork when clicking job url


# Class will be used by the GUI to access logic variables.
class UserInput:
    def __init__(
        self,
        url=None,
        fixed_low_rate=None,
        hourly_low_rate=None,
        # username=None,
        # password=None,
    ):
        self.url = url
        self.fixed_low_rate = fixed_low_rate
        self.hourly_low_rate = hourly_low_rate
        # self.username = username
        # self.password = password  # TODO: Username and password will be implemented in the future to open a logged in Upwork


#   !self.user_agent here ?????


def read_from_json(fallback_job_posts):
    """ Reads all the job posts from job_posts.json """
    try:
        with open("job_posts.json", "r") as job_posts_json:
            json_content = json.load(job_posts_json)
            return json_content
    except FileNotFoundError:
        print(
            "File not found – Attempting to create one."
        )  # !Remove this when code is working properly.
        json_content = {"Job Posts": fallback_job_posts}
        return json_content
        # TODO: Call function for running settings window


def write_to_json(job_post_list):
    """ Writes the latest web scrape to job_posts.json """
    json_dict = {"Job Posts": job_post_list}
    with open("job_posts.json", "w") as json_dump:
        json.dump(json_dict, json_dump, indent=4)


def extract_hourly_price(hourly_payment_type):
    """ Returns the hourly payment as int for message_printer() if-statement """
    # TODO: Put in try block and return empty string if error?
    if "-" in hourly_payment_type:
        # Accounts for job_post["Payment Type"] == "Hourly: $X.00–$Y.00"
        # Looking at the $Y to account for the payment range.
        return int(float(hourly_payment_type.split()[1].split("-")[1].lstrip("$")))
    else:
        # Accounts for job_post["Payment Type"] == "Hourly: $X.00"
        return int(float(hourly_payment_type.split()[1].lstrip("$")))


def extract_fixed_price(fixed_payment_type):
    """ Returns the fixed price as int for message_printer() if-statement """
    # Accounts for job_post["Budget"] == "$X"
    return int(fixed_payment_type.lstrip("$"))


def message_printer(new_job_posts):
    """ Prints number of new jobs (that satisfy user budget criteria) & their details """

    fixed_lowest_rate = 25

    hourly_lowest_rate = 0

    selected_new_job_posts = []

    for job_post in new_job_posts:
        # !print(job_post)  # Use this line to debug what job post might cause an error.
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
            print(job_post["URL"] + "\n")
    else:
        for job_post in selected_new_job_posts:
            print(job_post["Job Title"])
            if job_post["Payment Type"] == "Fixed-price":
                print(job_post["Payment Type"] + " " + job_post["Budget"])
            else:
                print(job_post["Payment Type"])
            print(job_post["Job Description"] + "...")
            print(job_post["URL"] + "\n")


def json_difference_checker(json_content, job_post_list):
    """Controls where in the new webscrape the highest job post in json is,
    to check amount of new posts"""

    old_job_urls = [job_post["URL"] for job_post in json_content["Job Posts"]]

    new_job_posts = [
        job_post for job_post in job_post_list if job_post["URL"] not in old_job_urls
    ]

    message_printer(new_job_posts)


def job_post_scraper(user_input):
    """ Scrapes Upwork for job posts and stores details in variables """
    # TODO: Set url to input to let people use other searches. (Write it to json)
    # TODO: Control that input is valid upwork search link. (Regex library)
    # TODO: Tell the user if there is no URL specified when trying to do request
    # url = "https://www.upwork.com/ab/jobs/search/?page=2&q=(translat%20OR%20proofread)%20AND%20swedish&sort=recency"

    url = user_input.url

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
            "URL": "https://upwork.com" + job_post_url,
        }

        job_post_list.append(job_post_dict)

    json_difference_checker(read_from_json(job_post_list), job_post_list)

    if job_post_list:
        write_to_json(job_post_list)


# job_post_scraper()  # TODO: Remove this when code is working
