## Basic usage:

Export QR images with titles into a {filename}_qr directory:
`python3 qr_generator.py {filename}.csv`

Export a PDF file of QR codes into a file {filename}_qr.pdf file
`python3 qr_grid.py {filename}.csv`

Export barcode images with titles into a {filename} directory:
`python3 barcode_generator.py {filename}.csv `

Export a PDF file of barcodes with titles into a {filename}.pdf directory:
`python3 barcode_grid.py {filename}.csv `

## How can I get the data for the files?

If you have access to your Grocy data you can run the below sql commands:

```
# sqlite command to get CreateBundles.csv data from your Grocy DB:
sqlite3 ~/codebases/grocy/config/data/grocy.db "SELECT 
  'CREATE/LC-' || p.location_id || 
  '/GRP-' || p.product_group_id || 
  '/QT-' || p.qu_id_purchase || 
  ',\"' || l.name || ', ' || pg.name || ', ' || qu.name || '\"' AS scan_csv_data
FROM 
  products p
JOIN 
  product_groups pg ON p.product_group_id = pg.id
JOIN 
  locations l ON p.location_id = l.id
JOIN 
  quantity_units qu ON p.qu_id_purchase = qu.id
WHERE l.id = 2 -- optionally filtering results by location
GROUP BY 
  p.product_group_id, p.location_id, p.qu_id_purchase
ORDER BY pg.name ASC, qu.name ASC, 
  COUNT(*) DESC;"
```
Save the output as a CSV at ./barcode_generator/CreateBundles.csv and use barcode_generator to create your QR codes (more info in barcode_generator/README.md)

```
# sqlite command to get Store.csv data from your Grocy DB:
sqlite3 ~/codebases/grocy/config/data/grocy.db "SELECT 
  'ST-' || t.id || ',' || t.name AS scan_csv_data
FROM 
  shopping_locations as t
ORDER BY t.name ASC"

# sqlite command to get Location.csv data from your Grocy DB:
sqlite3 ~/codebases/grocy/config/data/grocy.db "SELECT 
  'LC-' || t.id || ',' || t.name AS scan_csv_data
FROM 
  locations as t
ORDER BY t.name ASC"

# sqlite command to get Quantity.csv data from your Grocy DB:
sqlite3 ~/codebases/grocy/config/data/grocy.db "SELECT 
  'QT-' || t.id || ',' || t.name AS scan_csv_data
FROM 
  quantity_units as t
ORDER BY t.name ASC"

# sqlite command to get Category.csv data from your Grocy DB:
sqlite3 ~/codebases/grocy/config/data/grocy.db "SELECT 
  'GRP-' || t.id || ',' || t.name AS scan_csv_data
FROM 
  product_groups as t
ORDER BY t.name ASC"
```

If not, there are some sample files that you can modify. Note: Be sure to leave the text,title at the top of the CSV.

## Why?

Embed commands for the grocy_scanner_util app and call on those commands by scanning the right barcode.

Example: Scan mode changes before scanning your barcode to change the behavior of the app. By default, the barcode scanner is ready to "CONSUME" items that are scanned. 

When it's shopping day and you want to add things to your list, scan the "SHOPPING" barcode and any items you scan will be added to your shopping list. 

When you find something has spoiled, scan the "TRASHED" mode QR code and then the product barcode to wipe the currently open items from inventory. 

When you finish off a loaf of bread, scan the "FINISHED" mode and all your open inventory will be consumed. 

Use "CONSUME" mode to deduct the Quick Consume amount from your inventory. 

PURCHASE mode adds items back into your inventory, and if you scan the ST-{shopping_location_id} barcode you can set the store where you purchased the item. (prices and manually customized expiration dates not supported).

CREATE mode has additional configurations: Ways to set Quantity (QT-), Product Category (GRP-), and Location (LC-) by scanning those QR Codes, or scanning a "bundled" QR Code with multiple tags. Example: CREATE/LC-3/GRP-9/QT-9 would configure the scanner to create a new item in Location 3, with Product Category 9, and Quantity Unit 9. In this case, if I scanned this QR code before scanning a box of pasta, I will configure new products scanned to go directly into the "Pantry" as "Dry Goods" with quantity unit "Box". Scanning the box does an "external lookup" for the box and populates the name, but the other properties have to be manually assigned. If you're scanning all of your cans at the same time, you can configure the scanning util once per product type, and then just adjust as you move along.

If you scan the combination for CREATE/LC-3/GRP-9/QT-9 and then scan LC-8, your scanner util is now configured with LC-8, GRP-9, QT-9 and mode CREATE. 

"CLEAR-SCANNER" resets the properties in the app so that if you go from scanning the pantry to someplace else or from products at one store to another, you don't accidentally scan with the wrong values.

The barcode and QR generators create those configuration codes in printable sheets so you can reference them as you go through your inventory.