# Choosing A Terminal

The terminal is your primary way of interacting with files and running commands on Alliance Canada clusters (including Fir at SFU). Most operating systems include a built-in terminal (e.g., Command Prompt on Windows), but third-party tools often provide a better user experience.
## Windows - GitBash
- Download GitBash here: https://git-scm.com/download/win

- Install GitBash by running the Git-<version>-bit.exe you've downloaded. Select next for all options, leaving the default settings selected.

- When the installation is complete, select 'Launch Git Bash' and click on Finish
## MacOS - iTerm2
- Download iTerm2 here and follow the setup guide: https://iterm2.com/

## Customizing your terminal - Quality Of Life Improvements
One of the easiest ways to improve your workflow when working with ASE and Alliance Canada clusters is by setting up aliases in your terminal. Aliases let you create shortcuts for long commands, reducing repetitive typing and making your work more efficient.

To set these up, you'll need to edit your shell configuration file-commonly .bashrc or .bash_profile (depending on your system and terminal). For Git Bash, you can modify the .bash_profile file using the following commands:

Open for editing:
```bash
vi ~/.bash_profile
```
OR
```bash
vi ~/.bashrc
```
Save changes:
```bash
source ~/.bash_profile
```
OR
```bash
source ~/.bashrc
```
Inside the editor, press I to enter insert mode and add your custom aliases. Once finished, press ESC and type :wq (write and quit).

Here are some useful examples:

Login in to Alliance Canada cluster:
```bash
alias PUTANYTHINGHERE="ssh -X USERNAME@CLUSTER.alliancecan.ca"
```
Example:
```bash
alias fir="ssh -X jdoe@fir.alliancecan.ca"
alias graham="ssh -X jdoe@graham.alliancecan.ca"
alias nibi="ssh -X jdoe@nibi.alliancecan.ca"
```
## NEXT 
[Logging In To A Compute Canada Cluster](./logging-in-to-a-compute-canada-cluster.md)
