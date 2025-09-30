## General

- **What is Epiphyte?** A toolkit for database-backed neural data workflows. Epiphyte is built for working with continuous, dynamic stimuli and associated annotations or meta-data.
- **Where to configure DB access?** See `epiphyte/database/access_info.py`.

## Docker

- **`docker-compose up -d` doesn't work.** This line attempts to configure a datajoint database using an existing docker-image. To diagnose the issue, try running `sudo docker-compose ps`. If this returns nothing, the issue is likely with docker-compose. Make sure the install is correct and that the config files are in the expected place. Otherwise, check out the advice [here](https://github.com/docker/compose/issues/4181).

## MySQL Issues

- **`mysql -h 127.0.0.1 -u root -P 3306` doesn't work.** Depending on the error, a couple things could be wrong. Most commonly, the issue is that MySQL is not running in the background.
    - **`mysql not found`**:  
    *Possibly due to an issue with the path.*

        1. Try: `export PATH=${PATH}:/usr/local/mysql/bin` 
        2. re-run the original line. if the error is gone, add the above line to your `./bash-profile`. 
        3. if the path is not the issue, make sure that MySQL is properly installed. 

    - **`ERROR 2003 (HY000): Can’t connect to MySQL server on '127.0.0.1' (111)`**  
    *Likely cause: the MySQL server isn’t running (or is listening on a different port).*

        1. Check if MySQL is running:
            ```bash
            ps -Af | grep mysqld
            ```
            If you only see your shell/grep line like
            ```
            al       18214 18159  0 13:01 pts/4    00:00:00 grep mysqld
            ```
            then MySQL is **not** running.
        2. Start MySQL.
            - **Linux:**
            ```bash
            sudo systemctl start mysql.service
            # or (on some distros)
            sudo service mysqld start
            ```
            If you get `Failed to start mysqld.service: Unit mysqld.service not found.`, see the dedicated section below.
            - **macOS (Homebrew):**
            ```bash
            brew services start mysql@5.7
            ```
        3. Verify it’s running:
            ```bash
            ps -Af | grep mysqld
            ```
            Expected output includes a `mysqld` line, e.g.
            ```
            mysql    18365     1 30 13:04 ?        00:00:01 /usr/libexec/mysqld --basedir=/usr
            ```
        4. Find the listening port (default **3306**):
            ```bash
            sudo netstat -lnp | grep mysql
            ```
        5. Try logging in using that port:
            ```bash
            mysql -h 127.0.0.1 -u root -P <port>
            ```
        **Reference**: Troubleshooting steps and causes are discussed [here](https://www.tecmint.com/fix-error-2003-hy000-cant-connect-to-mysql-server-on-127-0-0-1-111/).

    - **`ERROR 1045 (28000): Access denied for user 'user'@'172.18.0.1' (using password: NO)`**  
        *Cause: authentication failed—no password was provided or server isn’t fully configured yet.*

        - **Fix**
        1. Force a password prompt:
            ```bash
            mysql -h 127.0.0.1 -u root -p
            ```
        2. When prompted, enter your password.  
            If you haven’t changed it and are using the default from your environment, use `simple`.
        3. Once authenticated, you should enter the MySQL monitor.

        > Security note: Change the default password once your database is stable (see the DataJoint/MySQL hardening guide).

    - **`ERROR 1698 (28000): Access denied for user 'root'@'localhost'`**  
        *Cause: root uses socket or another auth plugin; your CLI user isn’t permitted.*

        - **Fix (Linux)**
        1. Log in with sudo:
            ```bash
            sudo mysql -u root
            ```
        2. Create a local user mapped to your system account and grant privileges:
            ```sql
            USE mysql;
            CREATE USER 'YOUR_SYSTEM_USER'@'localhost' IDENTIFIED BY '';
            GRANT ALL PRIVILEGES ON *.* TO 'YOUR_SYSTEM_USER'@'localhost';
            UPDATE user SET plugin='auth_socket' WHERE User='YOUR_SYSTEM_USER';
            FLUSH PRIVILEGES;
            ```
        3. Restart MySQL:
            ```bash
            sudo service mysql restart
            ```

    - **`Failed to start mysqld.service: Unit mysqld.service not found.`**  
        *Cause: MySQL not installed (or a mismatched service name) on your distro.*

        - **Fix (Ubuntu)**
        1. Update package lists:
            ```bash
            sudo apt-get update
            ```
        2. Install MySQL server:
            ```bash
            sudo apt-get install mysql-server
            ```
        3. Start MySQL:
            ```bash
            sudo systemctl start mysql.service
            ```
        4. Verify:
            ```bash
            ps -Af | grep mysqld
            ```
            You should see a line like:
            ```
            mysql       7186       1  2 12:34 ?        00:00:00 /usr/sbin/mysqld
            ```

    - **Homebrew postinstall warning:**  
        **`Warning: The post-install step did not complete successfully.`** after `brew postinstall mysql@5.7`  
        *Cause: multiple/conflicting MySQL installs.*

        - **Fix**
        - See potential resolutions on this StackOverflow thread:  
            <https://stackoverflow.com/questions/50874931/the-post-install-step-did-not-complete-successfully-mysql-mac-os-sierra>

    - **SSL handshake when using DataJoint/Python:**  
        **`"Can't connect to MySQL server on '127.0.0.1' ([SSL: SSLV3_ALERT_HANDSHAKE_FAILURE]"`**  
        *Cause: DataJoint (as of Jan 2024) hasn’t supported Python > 3.9 in some setups; newer Python may trigger SSL handshake errors with `datajoint.conn()`.*

        - **Fix**
        - Use Python **3.7–3.9**, or create a fresh virtual environment pinned to ≤ 3.9 for DataJoint.
        - Then retry your connection.

    ---

    > After applying the relevant fix, you should be able to connect both from Terminal and from a Jupyter notebook. If an error persists, re-check that MySQL is running and that you are using the correct host/port/credentials.

