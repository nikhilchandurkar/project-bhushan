


<!-- database setup  -->

<!--  change fiields in square braces  -->

CREATE DATABASE [databse name] ;
CREATE USER [myuser] WITH PASSWORD ['mypassword'];
ALTER ROLE [myuser] SET client_encoding TO 'utf8';
ALTER ROLE [myuser] SET default_transaction_isolation TO 'read committed';
ALTER ROLE [myuser] SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE [database_name] TO [myuser];



<!-- cache setup -->

