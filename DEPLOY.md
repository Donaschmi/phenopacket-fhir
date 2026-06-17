# Deploying phenopacket-fhir to GitHub

Suggested repo name: **`phenopacket-fhir`**
Suggested description: *Map GA4GH Phenopackets v2 to FHIR R4 Questionnaire / QuestionnaireResponse — zero dependencies, pure Python*

---

## Step 1 — Create the GitHub repository

1. Go to https://github.com/new
2. Fill in:
   - **Repository name:** `phenopacket-fhir`
   - **Description:** `Map GA4GH Phenopackets v2 to FHIR R4 Questionnaire / QuestionnaireResponse — zero dependencies, pure Python`
   - **Visibility:** Public
   - Leave "Add a README file", ".gitignore", and "license" **unchecked** (they are already in the project)
3. Click **Create repository**
4. Copy the remote URL shown (e.g. `https://github.com/schmitzdonatien/phenopacket-fhir.git`)

---

## Step 2 — Open a terminal and navigate to the project

```bash
cd ~/Documents/Claude/Projects/Phenopackets
```

---

## Step 3 — Finish the initial git commit

The repo is already initialised and all files are staged. Just commit:

```bash
git add .
git commit -m "feat: initial release — Phenopackets v2 to FHIR Questionnaire/QuestionnaireResponse mapper"
```

---

## Step 4 — Push to GitHub

```bash
git remote add origin https://github.com/schmitzdonatien/phenopacket-fhir.git
git branch -M main
git push -u origin main
```

After this your code is live at `https://github.com/schmitzdonatien/phenopacket-fhir`.

---

## Step 5 (optional) — Add GitHub topics for discoverability

On the repo page, click the ⚙️ gear next to **About** and add these topics:

```
phenopackets  fhir  ga4gh  rare-disease  hl7  bioinformatics  interoperability  python
```

---

## Step 6 (optional) — Install the package locally for development

```bash
cd ~/Documents/Claude/Projects/Phenopackets
pip install -e ".[dev]"   # installs in editable mode + pytest
pytest                    # 26 tests should pass
```

---

## Ongoing workflow

```bash
# After making changes:
git add .
git commit -m "fix: describe your change"
git push
```
