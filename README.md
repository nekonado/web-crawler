# Web Crawler

## Project Overview

This project is a web crawler designed to scrape websites using a Docker environment. It fetches and records URLs, titles, and status codes of web pages starting from a specified URL. The project is implemented using Python and makes use of libraries such as `requests` and `beautifulsoup4`.

## Folder Structure

The project is organized as follows:

```bash
.
├── output/
├── .gitignore
├── crawler.py
├── crawler.sh
├── config.sample.json
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### Explanation of Files and Directories

### Explanation of Files and Directories

- **`output/`**: Directory for storing the crawling results in CSV format. The `.keep` file ensures the directory exists even if empty. After the crawler runs, CSV files are created in this directory, with filenames including a timestamp indicating the date of execution. The CSV files include the following columns:

  - **url**: The URL of the crawled page.
  - **title**: The title of the page.
  - **status_code**: The HTTP status code of the page.

  Example:

  ```csv
  url,title,status_code
  http://example.com,Example Domain,200
  http://example.com/page1,Page 1,200
  http://example.com/page2,Page 2,404
  ```

- **`.gitignore`**: Specifies files and directories to be ignored by Git. This includes `config.json` and any output files except `output/.keep`.

- **`crawler.py`**: The main Python script that implements the web crawling logic. It uses threading for concurrent requests and outputs results to a CSV file.

- **`crawler.sh`**: A shell script to create the output directory and execute the Docker Compose command to build and run the crawler.

- **`config.sample.json`**: A template configuration file. Users should rename this file to `config.json` and modify the values to suit their target site for crawling.

- **`Dockerfile`**: Used to create a Docker image for the crawler. It installs necessary Python packages and sets up the environment to run `crawler.py`.

- **`docker-compose.yml`**: Orchestrates the Docker container for running the crawler, defining services, volumes, and commands.

- **`requirements.txt`**: Lists the Python dependencies required for the crawler (`requests` and `beautifulsoup4`).

## Setup and Usage

### Prerequisites

- Docker and Docker Compose installed on your machine.
- Basic understanding of Docker and Python.

### Configuration

1. **Copy `config.sample.json` to `config.json`**:

```bash
cp config.sample.json config.json
```

2. **Edit `config.json`**:

   - **`start_url`**: The starting URL for the crawler. This should be the root page of the site you wish to crawl.
   - **`user_agent`**: The user agent string that the crawler will use when making HTTP requests. It is important to use a descriptive user agent to identify your crawler.
   - **`use_robots_txt`**: Boolean flag indicating whether the crawler should respect `robots.txt`. Set this to `true` or `false` depending on your requirements.

3. **Example `config.json`**:

### Building and Running the Crawler

1. **Build and run the Docker container**:

   Run the following command in the project directory:

```bash
./crawler.sh
```

This script will create the `output` directory (if it doesn't exist), build the Docker image, and start the crawling process using Docker Compose.

2. **Check the Output**:

   The results of the crawl will be saved in the `output` directory as two CSV files:

   - **`temp_yyyymmdd.csv`**: An temporary file that stores crawling data during the process.
   - **`crawl_result_yyyymmdd.csv`**: The final sorted output file where the results are saved after processing.

## Technical Details

### Crawling Logic

- **Concurrency**: The crawler uses Python's `concurrent.futures.ThreadPoolExecutor` to perform concurrent HTTP requests, improving performance.

- **Link Extraction**: Links are extracted using BeautifulSoup and normalized using `urllib.parse`. Only links within the same domain are followed.

- **Retry Mechanism**: The crawler retries failed requests up to three times with a delay between attempts.

- **Output**: The crawler records each visited URL, its title, and its HTTP status code in a CSV file.

### Docker and Docker Compose

- **Dockerfile**: Specifies a Python 3.9 slim image, installs dependencies, and copies the necessary scripts and configuration into the container.

- **docker-compose.yml**: Sets up the service for the crawler, mapping the local `output` directory to the container's `/app/output` to ensure results are accessible on the host machine.

## Notes

- Ensure that the `start_url` in `config.json` is correctly set to the root URL of the site you wish to crawl.
- The crawler's behavior can be modified by adjusting parameters like `MAX_RETRIES`, `DELAY_BETWEEN_REQUESTS`, and `NUM_THREADS` in `crawler.py`.

## Disclaimer

Use this crawler responsibly and adhere to the `robots.txt` guidelines and the website's terms of service. Make sure to set the `use_robots_txt` configuration appropriately to respect site policies.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/nekonado/web-crawler/blob/main/LICENSE) file for more details.
