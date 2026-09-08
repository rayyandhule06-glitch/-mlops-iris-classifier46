# DVC Workflow Documentation

## Overview

This project uses **Git** and **DVC (Data Version Control)** together to track dataset versions.

Git tracks the source code and DVC metafiles (`.dvc`), while DVC tracks the actual dataset files. This allows different versions of the dataset to be compared, restored, and reproduced along with the corresponding code.

## DVC Remote Configuration

The project uses a configured DVC remote to store the actual dataset objects.

The `.dvc` metafile stores metadata such as:

* MD5 hash of the dataset
* Dataset size
* Dataset path
* Hash type

The actual dataset is stored and versioned through DVC rather than directly in Git.

## DVC Workflow

For every dataset change, the following workflow is followed:

```text
Modify / Generate Dataset
        ↓
dvc add
        ↓
git add
        ↓
git commit
        ↓
dvc push
```

### 1. Add the dataset to DVC

```bash
dvc add data/raw/iris_v1.csv
```

This creates or updates:

```text
data/raw/iris_v1.csv.dvc
```

The `.dvc` file contains the hash and metadata required by DVC to identify the dataset version.

### 2. Stage the DVC metafile with Git

```bash
git add data/raw/iris_v1.csv.dvc
```

The dataset itself is not stored in Git. Instead, Git stores the `.dvc` metafile.

### 3. Commit the dataset version

```bash
git commit -m "data: add iris_v1 raw dataset"
```

Each dataset change receives a Git commit so that the corresponding `.dvc` pointer can be recovered later.

### 4. Push the dataset to the DVC remote

```bash
dvc push
```

This uploads the actual dataset object to the configured DVC remote.

### 5. Push Git commits

```bash
git push origin main
```

This uploads the Git commit containing the `.dvc` metafile and related project files.

## Dataset Version History

Two versions of the Iris dataset were created.

| Version   | Git Commit | Dataset Rows |
| --------- | ---------- | -----------: |
| Version 1 | `602aa4a`  |          150 |
| Version 2 | `6b8d972`  |          170 |

Version 1 was the original 150-row dataset. Version 2 added 20 synthetic rows, increasing the dataset from 150 to 170 rows.

The dataset-version history can be viewed with:

```bash
git log --oneline -- data/raw/iris_v1.csv.dvc
```

Expected commits:

```text
6b8d972 (HEAD -> main) data: augment iris dataset with 20 synthetic rows (150 -> 170)
602aa4a data: add iris_v1 raw dataset (150 rows) tracked via DVC
```

## Comparing Dataset Versions

DVC can compare the dataset in a previous Git commit with the current workspace.

```bash
dvc diff 602aa4a
```

This compares Version 1 with the current Version 2.

Expected output:

```text
Modified:
    data/raw/iris_v1.csv

files summary: 1 modified
```

This confirms that the dataset changed between the two versions.

## Comparing DVC Hashes

The DVC metafile from Version 1 can be viewed using:

```bash
git show 602aa4a:data/raw/iris_v1.csv.dvc
```

Version 1 contains:

```text
outs:
- md5: 21d441a28bce4417276097df955afc50
  size: 2928
  hash: md5
  path: iris_v1.csv
```

The current Version 2 metafile can be viewed using:

```bash
git show HEAD:data/raw/iris_v1.csv.dvc
```

Version 2 contains:

```text
outs:
- md5: 674c8c36bb7c4ba8d851dee9e6ee67af
  size: 4462
  hash: md5
  path: iris_v1.csv
```

The different MD5 hashes confirm that the underlying dataset changed.

## Restoring a Historical Dataset Version

To temporarily restore Version 1, first restore its DVC metafile:

```bash
git checkout 602aa4a -- data/raw/iris_v1.csv.dvc
```

Then restore the corresponding dataset from the DVC cache:

```bash
dvc checkout data/raw/iris_v1.csv.dvc
```

The restored Version 1 dataset can be verified with:

```bash
wc -l data/raw/iris_v1.csv
```

Expected result:

```text
151 data/raw/iris_v1.csv
```

This represents 150 data rows plus the header row.

## Restoring the Latest Dataset Version

To restore the latest Version 2 DVC metafile:

```bash
git checkout HEAD -- data/raw/iris_v1.csv.dvc
```

Then restore the latest dataset:

```bash
dvc checkout data/raw/iris_v1.csv.dvc
```

Verify the dataset:

```bash
wc -l data/raw/iris_v1.csv
```

Expected result:

```text
171 data/raw/iris_v1.csv
```

This represents 170 data rows plus the header row.

## Dataset Generation and Augmentation

The project also contains scripts used to generate and augment the dataset:

```text
src/generate_data.py
src/augment_data.py
```

These scripts are tracked by Git so that the code used to create or modify a dataset can be reproduced.

They can be committed using:

```bash
git add src/augment_data.py src/generate_data.py
git commit -m "feat: add dataset generation and augmentation scripts"
git push origin main
```

## Final Verification

The current DVC metafile can be inspected with:

```bash
cat data/raw/iris_v1.csv.dvc
```

The dataset version history can be checked with:

```bash
git log --oneline -- data/raw/iris_v1.csv.dvc
```

The Git working tree can be checked with:

```bash
git status
```

A clean working tree should report that there is nothing to commit.

## Conclusion

The project uses Git and DVC together for reproducible dataset versioning.

Git tracks the code and DVC metafiles, while DVC tracks the actual dataset contents. The combination of `dvc add`, `git commit`, `dvc push`, `dvc diff`, and `dvc checkout` makes it possible to version, compare, restore, and reproduce different dataset states.

This workflow ensures that experiments can be reproduced using the appropriate version of both the code and the data.
