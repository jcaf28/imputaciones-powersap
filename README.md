# suite-ip
Página web para alojar aplicaciones para adaptar las imputaciones del powerapps a SAP de div3

# dev:
docker-compose up --build

# prod
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# run basic tests
./test.sh
