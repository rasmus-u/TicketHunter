# How to use:
1. Clone the project to local directory with\
`git clone git@github.com:rasmus-u/TicketHunter.git`
3. To install dependencies in an virtual envinronment run the following commands:

On Mac:
  ```
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```
  On Windows:
  ```
  python -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt
  ```

3. Rename `.env-template` file to `.env`
4. Fill at least the following fields inside the `.env` file

```
EMAIL=
PASSWORD=
URL=
MIN_PRICE=
MAX_PRICE=
MAX_FAILED_ATTEMPTS=
```

  - `EMAIL`: kide.app account email address
  - `PASSWORD`: kide.app account password
  - `URL`: `https://kide.app/events/[event number]` the entire url that leads to the ticket page
  - `MIN_PRICE`: the estimate of ticket minimum price
  - `MAX_PRICE`: the estimate of ticket maximum price
  - `MAX_FAILED_ATTEMPTS`: the amount of attemts the bot makes before giving up, recommended value: 10
5. Use the virtual environment set up earlier (run ```source venv/bin/activate``` or ```venv\Scripts\activate``` if you have already closed this command 
line window)
Run the bot with the command ```python tickethunter.py```
6. After completion, the tickets can be redeemed by logging into your account

### There are some known bugs with the bot but the core functionality works, the bot buys the tickets very effectively

