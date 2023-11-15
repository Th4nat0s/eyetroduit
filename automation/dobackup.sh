cd ..
datetime=$(date +\%Y\%m\%d\%H\%M\%S)
scp root@161.35.82.54:/var/www/eyetroduit/app.db backup/database_$datetime.db
cd backup
bzip2 -9 database_$datetime.db
cd ..

