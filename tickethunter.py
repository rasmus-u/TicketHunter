import requests
import json
import time
import asyncio
import sys
import os
from getpass import getpass
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

def getAuth(user, passw):
  domain = "https://auth.kide.app/oauth2/token"
  authData = "client_id=56d9cbe22a58432b97c287eadda040df&grant_type=password&password={}&rememberMe=true&username={}".format(passw, user)
  token = json.loads(requests.post(url=domain, data=authData).content)["access_token"]
  return {"authorization": "Bearer {}".format(token)}

def getDomainID(url: str):
  return url.split("/")[-1]

def getProductVariants(productID: str):

  global saleTime

  baseDomain = "https://api.kide.app/api/products/"
  domain = baseDomain + productID
  productVariants = []

  #Testing tool
  count = 0  
  product = json.loads(requests.get(url=domain).content)["model"]
  saleTimeRaw = product["product"]["dateSalesFrom"]
  saleTime = datetime.strptime(saleTimeRaw.split("+")[0].split("T")[1], '%H:%M:%S')

  print("Sale begins at", str(saleTime).split(" ")[1])

  while len(productVariants) == 0:
    productVariants = product["variants"]
    sys.stdout.write('\rTrying to find tickets \\ ')
    time.sleep(0.1)
    sys.stdout.flush()
    sys.stdout.write('\rTrying to find tickets / ')
    time.sleep(0.1)
    sys.stdout.flush()
    

  print("Tickets found on page")
  return productVariants

def parseProductDetails(productData):
  items = []
  for product in productData:
    if not product["isProductVariantMarkedAsOutOfStock"] and product["isProductVariantTransferable"] and not product["isProductVariantHakaAuthenticationRequired"]:
      item = {
        "inventoryID": product["inventoryId"],
        "name": product["name"],
        "price": product["pricePerItem"], #marked as 100x the actual price in euros
        "max_amount": min(product["availability"], product["productVariantMaximumItemQuantityPerUser"], product["productVariantMaximumReservableQuantity"])
      }
      items.append(item)
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
  
async def getProduct(inventoryID, amount, loginToken):

  global saleTime
  global failedAttempts
  
  fail_tolerance = int(os.getenv('MAX_FAILS_ATTEMPTS'))

  begins = datetime.now().replace(hour=saleTime.hour, minute=saleTime.minute + 1) #Current time +1 min
  

  while begins < datetime.now() and quantityReceived < amount and failedAttempts < fail_tolerance:
    firstTask = ()
    for i in list(range(max(1, quantityReceived), amount + 1)):
      task = asyncio.create_task(bombProduct(inventoryID, i, loginToken))
      if i == max(1, quantityReceived): #i is the first element
        firstTask = task
    await firstTask

  print("Tickets received:", str(quantityReceived))
  print("\nTickets are in the shopping cart for 25 minutes. Login to your account to pay for the tickets and redeem them.")
    
def main():
  username = str(os.getenv('EMAIL'))
  password = str(os.getenv('PASSWORD'))
  url = str(os.getenv('URL'))

  print("\n\nStarting the ticket hunter software\n\n\n")

  DomainID = getDomainID(url)
  print("Domain found\nTrying to login to Kide.App")
  
  loginToken = getAuth(username, password)
  print("Login successful!")

  
  minprice = str(str(os.getenv('MIN_PRICE')).replace(",","."))
  maxprice = float(str(os.getenv('MAX_PRICE')).replace(",","."))
  if len(minprice) == 0: minprice = 0
  else: minprice = float(minprice)
  print("Beginning the hunt...\n")

  data = getProductVariants(DomainID)
  products = parseProductDetails(data)
  (id, amount) = findProductID(products, maxprice, priceMin=minprice)
  asyncio.run(getProduct(id, amount, loginToken))

main()


