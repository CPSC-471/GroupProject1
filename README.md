# GroupProject1

## Project Members:
  * Jeffrey Lo     - jeffylo94@csu.fullerton.edu
  * Mike Souchitto - asdefmike@csu.fullerton.edu
  * Joseph Chau    - Flyballer@csu.fullerton.edu


## About Project:
   Part of CSUF CPSC-471 Group GroupProject1
   Goal: Simple FTP Server/Client
   Programming Language: Python 3.7
   Requires Linux/Mac OS

   * can only browse files within folder containing serverside.py
   * client side files are placed in folder containing clientside.py
   * because of this, you should consider placing serverside and clientside in seperate directories.

## How to Set Up:
  * Permissions:
    * Enable read write permissions for ServerSide.py and ClientSide.py if necessary

  * Server Setup
  ```
  > Python3.7 ServerSide.py <port>

  //For Example: Python3.7 ServerSide.py <1234>
  ```

  * Client Setup
  ```
  > Python3.7 ClientSide.py <ip> <port>

  // For Example: Python3.7 ClientSide.py <localhost> <1234>

  ```

## Client Commands:
   * #### get
   ```
   JMJftp> get <path>

   //For example: get exampleDir/sampleFile1.txt
   ```
   * #### put
   ```
   JMJftp> put <path>

   //For example: get exampleDir/sampleFile1.txt
   ```
   * #### ls
   ```
   JMJftp> ls <path - optional>
   ```
   * #### quit
   ```
   JMJftp> quit
   ```
