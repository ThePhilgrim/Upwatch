import requests
from bs4 import BeautifulSoup
import json
import time

# import re  # For looking for eventual word counts in job posts & controlling the validity of url input


def read_from_json():
    """ Reads all the job posts from job_posts.json """
    try:  # Not sure if I need a try block
        with open("job_posts.json", "r") as job_posts_json:
            json_content = json.load(job_posts_json)
            return json_content
    except FileNotFoundError:
        return


def write_to_json(job_post_list):
    """ Writes the latest web scrape to job_posts.json """
    json_dict = {"Job Posts": job_post_list}
    with open("job_posts.json", "w") as json_dump:
        json.dump(json_dict, json_dump, indent=4)


def message_printer(index, job_post_list):
    """ Prints number of new jobs & their details """
    if index == 0:
        print("No New Job Posts")  # TODO: Remove this and exhange for return
    elif index == 1:
        print(
            f"""There is {index} new job post.
        """
        )
    else:
        print(
            f"""There are {index} new job posts.
        """
        )
    job_post_index = 0

    if index >= 4:
        for job_post in job_post_list[:index]:
            if job_post["Payment Type"] == "Fixed-price":
                print(
                    f"{job_post['Job Title']} – {job_post['Payment Type']}: {job_post['Budget']}"
                )
            else:
                print(f"{job_post['Job Title']} – {job_post['Payment Type']}")
            if job_post_index == index - 1:
                print(job_post["URL"])
            else:
                print(job_post["URL"] + "\n")
            job_post_index += 1
    else:
        for job_post in job_post_list[:index]:
            print(job_post["Job Title"])
            if job_post["Payment Type"] == "Fixed-price":
                print(job_post["Payment Type"] + " " + job_post["Budget"])
            else:
                print(job_post["Payment Type"])
            print(job_post["Job Description"] + "...")
            if job_post_index == index - 1:
                print(job_post["URL"])
            else:
                print(job_post["URL"] + "\n")
            job_post_index += 1


def json_difference_checker(json_content, job_post_list):
    """Controls where in the new webscrape the highest job post in json is,
    to check amount of new posts"""
    # TODO: Add if json_content['Job Posts'][0]['URL'] not in job_post_list ->
    # Use json_content['Job Posts'][1]['URL'] & index start at -1 (I think, so user don't get 1 extra job post as "new")

    previous_top_post = json_content["Job Posts"][0]["URL"]

    index = 0

    for job_post in job_post_list:
        if job_post["URL"] == previous_top_post:
            break
        index += 1

    message_printer(index, job_post_list)


def job_post_scraper():
    """ Scrapes Upwork for job posts and stores details in variables """
    # TODO: Set url to input to let people use other searches.
    # TODO: Control that input is valid upwork search link.
    url = "https://www.upwork.com/ab/jobs/search/?q=(translator%20OR%20translation%20OR%20proofread)%20AND%20swedish&sort=recency"

    connection_attempts = 0

    while connection_attempts < 3:
        try:
            html = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
                },
                timeout=3
            ).text  # TODO: Figure out how to fetch User Agent on current system.
        # html.raise_for_status()  # TODO: Find out why this doesn't work ("AttributeError: 'str' object has no attribute 'raise_for_status'")
            break
        except requests.exceptions.HTTPError as errh:
            print("HTTP Error:", errh)
            print("Please try a different URL")
        # except requests.exceptions.ConnectionError as errc:
        #     print("Error Connecting:", errc)
        #     print("Please check you internet connection and try again.")
        #     return
        except requests.exceptions.Timeout as errt:
            print("Your request timed out.")
            time.sleep(30)
            print("Trying again...")
            connection_attempts += 1

    soup = BeautifulSoup(html, "lxml")

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

        # TODO: Add logic for a "don't bother me rate" – if payment type == fixed-price and budget <= X: DELETE
        # if payment type == Hourly and hourly rate <= X: DELETE

        job_post_list.append(job_post_dict)

    json_difference_checker(read_from_json(), job_post_list)  # TODO: Add conditional if json is empty (first time using the program)

    if job_post_list:
            write_to_json(job_post_list)  # TODO: This needs to go in an if statement to make sure json doesn't get emptied on failure


job_post_scraper()
