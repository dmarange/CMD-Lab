# Setting Up Python On Compute Canada Cluster

Compute Canada clusters, such as Cedar and Graham, come with many pre-installed modules and applications, including Python. However, these system-wide installations cannot be customized to suit your specific needs. To properly set up ASE, it is recommended that you install your own personal Python environment within your cluster account.

- In your $home, create a folder (virtenv) that will be the path to the virtual environment containing Python:

```bash
python -m venv virtenv
```
- Activate the virtual environment using:

```bash
source ~/virtenv/bin/activate
```
- You'll see the terminal-user change to something like:

```
(virtenv) [username@cedar1 ~]$
```
- Verify that the Python path is directed to your virtual environment directory using:

```bash
which python
```
The path should include your virtual environment directory.
##NEXT
[Setting Up ASE On Compute Canada Cluster](./setting-up-ase-on-compute-canada-cluster.md)
