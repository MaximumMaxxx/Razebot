# Commands
### All commands are slash based.

Parameters are seperated by spaces, and can be in any order. () is an optional parameter. [] is a required parameter.

One other note:

Quick acounts are accounts **you don't own** but want to be able to check more easily. These might be the accounts of your friends or of streamers.

Myaccounts are **accounts that you own**. These accounts are used for rank assignment and when someone uses /rankcheckuser. 

---

## Rank checks

### /rankcheckaccount [account] (region)
Checks the stats of the account. If no region is specified it will use whatever region you have set for the server. You can check the region by pinging the bot.


### /rankcheckuser [discord user] (region)
Prompts you to choose from the user's `myaccounts` list. If no region is specified it will use whatever region you have set for the server. You can check the region by pinging the bot.


### /rclist [myaccounts/quickaccounts]
Prompts you to choose from your `myaccounts` or `quickaccounts` list. Once an account is selected the bot will check the stats of that account.

---

## Account management

### [my/quick]accounts list
Lists all the accounts you have in the specified list.

### [my/quick]accounts add [account] [region] (note)
Adds an account to the specified list. If no note is specified it will default to "No note".

### [my/quick]accounts remove [account]
Removes an account from the specified list.

---
## Role assignment

### /setroles [role] [rank]
Sets the role that the bot will assign to a user based on their in game rank.

### /updaterole
Updates the roles based on the ranks of all the accounts in your `myaccounts` list.

---

## Other commands

### /settings [setting] [value]
Allows you to change settings.

list of all settings:
```
region: Na, Eu, Kr, Ap 
```


### /test
Makes sure the api's are working. If the bot repeatedly gives you the message "Razebot is being rate limited" try this.
