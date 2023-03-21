# How to use:
1. Pull the project to local directory
2. Rename `.env-template` file to `.env`
3. Fill the details inside the .env file

```
EMAIL=
PASSWORD=
URL=
MIN_PRICE=
MAX_PRICE=
MAX_FAILED_ATTEMPTS=
```

  - EMAIL: kide.app account email address
  - PASSWORD: kide.app account password
  - URL: `https://kide.app/events/[event number]`
  - MIN_PRICE: the estimate of ticket minimum price
  - MAX_PRICE: the estimate of ticket maximum price
  - MAX_FAILED_ATTEMPTS: the amount of attemts the bot makes before giving up, recommended value: 10
4. Run the python file in working directory with
```
python tickethunter.py
```
  Don't do this too early before the sale begins as it may flood the servers. Recommended to start 3 minutes before the sale.
5. After completion, the tickets can be redeemed by loggin into your account

