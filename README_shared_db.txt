Shared DB version of microservices_shop_demo

Changes made:
1. product_db + order_db merged into one Redis service: shop_db
2. product_service now seeds products both on GET / and POST /reduce_stock
3. order_service now connects to shop_db and shows the updated DB label

Run:
  docker compose down -v
  docker compose up --build -d --scale product_app=3 --scale order_app=2

Open:
  http://localhost:8080/order/
  http://localhost:8080/product/
