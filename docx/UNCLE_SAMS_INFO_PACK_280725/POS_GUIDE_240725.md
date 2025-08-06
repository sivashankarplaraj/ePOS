# POS
Specification											Date   24/07/25
--------------------------------------------------------------------------------------------------------------------------------------------------------
Section 1 – Automation
Should be able to update the system with the latest data of products (eg, prices, availability of products at shop, product description, stock components) at any time.
Should be able to change the price bands operated by the shops and delivery companies at any time.
A delivery company can be operated at different price bands at different shops.
Different shops can have different OTC product prices.
For example, Montpelier Road shop has “Standard” price while Portsmouth shop has “Standard (B)” price. “Standard (B)” product prices are lower than “Standard” product prices.
Section 2 – Functions
Enter order  (Take away or Eatin)
Accept the following payment methods
- Cash
- Card
- On Account payment
- Voucher
Enter crew food
Enter crew ID to run this option
We may enter either 0 or a valid crew ID
Enter cooked waste
Enter crew ID to run this option
We may enter either 0 or a valid crew ID
Enter Paid out
Enter crew ID to run this option
We may enter either 0 or a valid crew ID
Paid out at any one time must be less than £1000.
Print receipt
The current order
An order taken today
An order taken on a previous day
Check total value of an order
To display the current order with the amount due.
If the customer pays by card, then the amount due will include any card fee.
If the total value of order is greater than or equal to the card minimum price, which is a shop variable, then we do not charge card fee.
Till reading
To close the shift and get the till reading on the screen.
Display the total value of the following items entered into the system via this till today:
Cash
Card
On Account
Vouchers
Paid outs
Crew food
Cooked waste
Deletes
Till Report
To print Uncle Sams Till Report
- Toggle payment for a given order
For a chosen order, no matter what price was used (eg  Standard, Deliveroo – Deliver, Just Eat – Collect),  we can change the method of payment if
the order was a take away or eatin, and
the order was not paid by a mixed payment (eg  paid by £8.40 cash and £5 voucher)
Recall today’s orders
To delete an order
To print a receipt for an order
To toggle payment for an order
Recall previous days’ orders
To delete an order
To print a receipt for an order
To toggle payment for an order
Memory Box
To display the previous order (which was either taken or cancelled) on screen and allow the user to select items from the previous order to be added to the current order list.
Void current order
Allow the user to cancel the current order before they press take away or eat here key.
Cancel Product
To cancel the current item from the current order.
Subtract Product
To delete any of the items entered before the current item in the current order.
Each delivery company accepts certain types of payment – Cash, Card, On Account payment. Return error message if the user enters a payment method which is not accepted by the delivery company.
When we start an order taking process, the program checks if the cooker limit or fryer limit is reached. If any of the limits is reached, it displays a warning message telling the cashier not to take any more orders.
Section 3 – Generate files
Record details of orders and payments.
Generate daily CSV files and K_WK_VAT.csv after the shop has closed the POS and has done a Z reading at night.
Print reports
On Account Payments – By Companies
Takings by Companies
-----  END  -----