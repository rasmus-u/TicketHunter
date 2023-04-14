import requests
import json
import time
import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()

quantityReceived = 0
saleTime = ""
failedAttempts = 0

# 1. Get [PRODUCT ID] from domain
# 2. Spam GET to https://api.kide.app/api/products/[PRODUCT ID]
# 3. When GET response model/variants has length of over 1 stop
# 4. Go through the products and decide which to buy based on parameters and save inventoryID
# 5. Spam GET to https://api.kide.app/api/reservations with correct inventoryID

def getAuth(credentials):
  domain = "https://auth.kide.app/oauth2/token"
  authDetails = []
  for credential in credentials:
    authData = "client_id=56d9cbe22a58432b97c287eadda040df&grant_type=password&password={}&rememberMe=true&username={}".format(credential[1], credential[0])
    try:
      token = json.loads(requests.post(url=domain, data=authData).content)["access_token"]
      authDetails.append(( str(credential[0]), {"authorization": "Bearer {}".format(token)} ))
    except:
      print('Error with account', str(credential[0]))

  return authDetails

def getDomainID(url: str):
  return url.split("/")[-1]

def getProductVariants(productID: str):

  global saleTime

  baseDomain = "https://api.kide.app/api/products/"
  domain = baseDomain + productID
  productVariants = json.loads(requests.get(url=domain).content)["model"]["variants"]

  product = json.loads(requests.get(url=domain).content)["model"]
  saleTimeRaw = product["product"]["dateSalesFrom"]
  saleTime = datetime.strptime(saleTimeRaw.split("+")[0].split("T")[1], '%H:%M:%S')

  print("Sale begins at", str(saleTime).split(" ")[1])

  while len(productVariants) == 0:
    time_difference = (saleTime.replace(year=datetime.now().year, day=datetime.now().day, month=datetime.now().month)-datetime.now()).total_seconds()
    if (time_difference > 80):
      time.sleep(2)
      sys.stdout.write('\rWaiting / ')
      time.sleep(2)
      sys.stdout.write('\rWaiting - ')
      time.sleep(2)
      sys.stdout.write('\rWaiting \\ ')
      time.sleep(2)
      sys.stdout.write('\rWaiting | ')
    else:
      productVariants = json.loads(requests.get(url=domain).content)["model"]["variants"]
      if time_difference > 2:
        sys.stdout.write('\rTrying to find tickets / ')
        time.sleep(0.1)
        sys.stdout.write('\rTrying to find tickets - ')
        time.sleep(0.1)
        sys.stdout.write('\rTrying to find tickets \\ ')
        time.sleep(0.1)
        sys.stdout.write('\rTrying to find tickets | ')
      else:
        time.sleep(0.1)
    

  print("Tickets found on page")
  return productVariants

def parseProductDetails(productData):
  items = []
  containsUntransferableItems = False
  for product in productData:
    if not product["isProductVariantMarkedAsOutOfStock"] and not product["isProductVariantHakaAuthenticationRequired"]:
      item = {
        "inventoryID": product["inventoryId"],
        "name": product["name"],
        "price": product["pricePerItem"], #marked as 100x the actual price in euros
        "max_amount": min(product["availability"], product["productVariantMaximumItemQuantityPerUser"], product["productVariantMaximumReservableQuantity"])
      }
      items.append(item)
    containsUntransferableItems = product["isProductVariantTransferable"]
  
  if containsUntransferableItems: print("Warning! Some of the items are untransferable between accounts. Beware when paying for them!")

  return items

def findProductID(productList, priceMax, priceMin=0, name=None, sortByCheapest=False):
  # No support for name filtering as of yet

  print("Looking for a matching ticket")
  filteredProducts = list(filter(lambda product: product["price"] >= priceMin*100-90 and product["price"] <= priceMax*100
  +90, productList))
  if len(filteredProducts) == 0: filteredProducts = productList
  if sortByCheapest: 
    print("Product ID found")
    wantedItem = max(filteredProducts, key=lambda product: product["price"])
    return (wantedItem["inventoryID"], wantedItem["max_amount"])
  else:
    print("Ticket found")
    return (filteredProducts[0]["inventoryID"], filteredProducts[0]["max_amount"])
  
async def getProduct(inventoryID, amount, loginTokenList):

  global saleTime
  global failedAttempts
  global quantityReceived
  
  fail_tolerance = int(os.getenv('MAX_FAILED_ATTEMPTS'))

  end_time = datetime.now().replace(hour=saleTime.hour, minute=saleTime.minute + 1) #Current time +1 min
  
  dev_mode = True if (os.getenv('DEVELOPER_MODE')).lower() == 'true' else False
  
  for credentials in loginTokenList:
    quantityReceived = 0
    failedAttempts = 0

    print("\nBuying tickets for", str(credentials[0]))
    
    # EDIT ON TESTING (< when testing, > when production)
    while (end_time > datetime.now() or dev_mode) and quantityReceived < amount and failedAttempts < fail_tolerance:
      firstTask = ()
      for i in list(range(max(1, quantityReceived), amount + 1)):
        task = asyncio.create_task(bombProduct(inventoryID, i, credentials[1]))
        if i == max(1, quantityReceived): #i is the first element
          firstTask = task
      await firstTask
    print("Received", str(quantityReceived), "for account", str(credentials[0]))
    

  print("\nTickets are in the shopping cart for 25 minutes. Login to your account to pay for the tickets and redeem them.")
  print("https://kide.app/")

async def bombProduct(inventoryID, amount, loginToken):

  global quantityReceived
  global failedAttempts

  buylocation = "https://api.kide.app/api/reservations"
  payload = {
      "toCreate": [
          {
              "inventoryId": inventoryID,
              "quantity": amount,
              "productVariantUserForm": None
          }
      ],
      "toCancel": []
    }
  response = requests.post(url=buylocation, json=payload, headers=loginToken).content

  old = quantityReceived
  try: 
    quantityReceived = max(json.loads(response)["model"]["reservations"][0]["reservedQuantity"], quantityReceived)
    if old != quantityReceived: print("Trying ticket amount", str(quantityReceived), " - success")
  except: 
    print("Trying ticket amount", str(amount), " - failed")
    failedAttempts += 1
  
    
def main():
  creds = [( str(os.getenv('EMAIL')), str(os.getenv('PASSWORD')) )]

  url = str(os.getenv('URL'))

  #If any other credentials provided
  if str(os.getenv('EMAIL2')) != '' or str(os.getenv('EMAIL2')) != None:
    creds.append( (str(os.getenv('EMAIL2')), os.getenv('PASSWORD2')) )

  if str(os.getenv('EMAIL3')) != '' or str(os.getenv('EMAIL3')) != None:
    creds.append( (str(os.getenv('EMAIL3')), os.getenv('PASSWORD3')) )

  print("\n\nStarting the ticket hunter software\n\n\n")

  DomainID = getDomainID(url)
  print("Domain found\nTrying to login to Kide.App")
  
  loginTokenList = getAuth(creds)
  print("Login successful!")

  
  minprice = str(str(os.getenv('MIN_PRICE')).replace(",","."))
  maxprice = float(str(os.getenv('MAX_PRICE')).replace(",","."))
  if len(minprice) == 0: minprice = 0
  else: minprice = float(minprice)
  print("Beginning the hunt...\n")

  data = getProductVariants(DomainID)
  products = parseProductDetails(data)
  (id, amount) = findProductID(products, maxprice, priceMin=minprice)
  asyncio.run(getProduct(id, amount, loginTokenList))

  with open("statistics.json", "w") as file:
    ticket_details = {"ticket bought": id, "amount bought": amount}
    stats = [ticket_details, data]
    json.dump(stats, file)

main()

# Make the bot more aggressive by not trying to spam buy when availability doesn't allow it
# Successfully buying ticket gives info on current availability, first buy one and then try to buy 50% of the availability progressively
# Make this a rage-mode option