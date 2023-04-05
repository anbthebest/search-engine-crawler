🔎 Onion Search Engine
Onion Search Engine is a web application that allows users to search for content on the Tor network. This search engine is designed to run on the Flask framework and uses SQLite3 to store search results. The purpose is store and retrieve links with onion format, it has a several regEx and fucntions for example there is a function called search() that performs two main tasks. The first task is to check if there are any search results already stored in the database for the given keyword. If there are no search results, it scrapes the search engines provided in the code for links containing the keyword and saves them to the database.

The second task is to retrieve the stored search results from the database and display them to the user in a paginated format.

In order to accomplish the first task, the search() function uses a list of search engine URLs provided in the code to scrape the search engines for links containing the keyword. The scraped links are then stored in a SQLite database along with a unique identifier for the search term, which is generated using the SHA-256 hashing algorithm.

In order to accomplish the second task, the search() function retrieves the stored search results from the database using the unique identifier generated for the search term. The retrieved results are then displayed to the user in a paginated format.

The search() function makes use of several helper functions, such as connect_db() to connect to the SQLite database, count_total_rows_in_table() to count the total number of rows in a given table, and hashlib.sha256() to generate a unique identifier for the search term.

Overall, the search() function and its helper functions work together to store new search results and retrieve them for display to the user.

🚀 Getting Started
To run this application, you will need to have Python 3.x and the required dependencies installed on your system. You can install the dependencies by running the following command:

bash
Copy code
pip install -r requirements.txt
Once you have installed the dependencies, you can run the application by executing the following command:

bash
Copy code
python main.py
📝 Usage
Once you have the application running, you can access it by navigating to http://localhost:5000/ in your web browser.

To search for content on the Tor network, enter your search query in the search bar and click the "Search" button. The search results will be displayed on the next page.

🧪 Testing
To run the test suite, execute the following command:

bash
Copy code
python test.py
📦 Dependencies
Onion Search Engine relies on the following dependencies:

Flask
Flask-WTF
Flask-Limiter
Flask-Caching
Werkzeug
Beautiful Soup 4
requests
PySocks
stem
geoip2
📄 License
Onion Search Engine is released under the MIT License. See LICENSE for more information.

Now the Frontend features

🌟 Onion Search Engine Front-End Project 🌟
This is a cool front-end project that I built using HTML, CSS, and JavaScript. It's a single-page application that allows users to search for and view information about different animals.

🚀 Getting Started
To run this project on your local machine, follow these steps:

Clone the repository
Open index.html in your web browser
Enjoy!
💻 Technologies Used
HTML
CSS
JavaScript
jQuery
🎨 Features
Search for animals by name or category
View detailed information about each animal
Responsive design for mobile devices
🤝 Contributing
If you'd like to contribute to this project, feel free to submit a pull request or open an issue.

📝 License
This project is licensed under the MIT License - see the LICENSE.md file for details.