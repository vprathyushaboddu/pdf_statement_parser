# Bank Statement PDF-to-Excel Parser — Project Requirements Document

**Status:** Draft v1.0
**Owner:** Anil (personal finance use)
**Last updated:** 2026-07-20

---

## 1. Purpose

This document defines the requirements for a desktop tool that converts digital (text-based)
bank statement PDFs into a structured Excel file, with one row per transaction, correctly
mapped into a fixed set of columns.

The tool is for personal use — organizing the user's own bank statements for tracking,
budgeting, and record-keeping.

---

## 2. Problem Statement

Bank statements are issued as PDFs with inconsistent layouts across banks: different column
orders, header wording, date formats, multi-line transaction descriptions, and page-break
artifacts (repeated headers/footers, page numbers, running balance text). A generic
"PDF-to-text" or "PDF-to-table" converter does not reliably solve this — it either mangles
rows that span multiple lines, misreads which number is debit vs. credit vs. balance, or
requires manual cleanup after every export.

What's needed instead is a tool that **understands the structure of each supported bank's
statement format** and reliably extracts transactions from it — not a dumb layout-to-grid
conversion.

---

## 3. Goals

- Reliably extract every transaction from a supported bank's statement PDF, with no missed,
  duplicated, or merged rows.
- Correctly place each transaction's data into the right Excel column, every time.
- Support multiple banks, each potentially with its own statement layout, through
  bank-specific parsing logic (not one brittle universal regex).
- Produce a clean, ready-to-use Excel file with no manual touch-up required for the
  supported cases.
- Be usable by a non-technical end user (the user themself) via a simple desktop UI —
  no command line, no scripts to edit.

## 3.1 Non-Goals (for v1)

- OCR / scanned (image-based) PDF support. Input is assumed to be text-based/selectable PDF.
- Cloud hosting, multi-user accounts, or a web-based service.
- Automatic bank/format detection for *arbitrary, unknown* banks — only banks that have been
  explicitly added and tested are supported (see §7).
- Categorization/tagging of transactions (e.g. "groceries", "rent") — output is raw
  transaction data only.
- Reconciliation, budgeting, or reporting features. This tool's job ends at producing the
  Excel file.

---

## 4. Users

| User | Description |
|---|---|
| Primary user | The account owner, using the tool on their own machine for their own bank statements. Not a developer workflow — should feel like a normal desktop app. |

Since this is single-user/personal-use, requirements around multi-tenancy, access control,
and audit trails are explicitly out of scope.

---

## 5. Functional Requirements

### 5.1 Input handling

- FR-1: The user can select one or more PDF files (or a folder) via the desktop UI.
- FR-2: The tool must detect which bank a given PDF belongs to, either automatically
  (e.g. by matching known header/logo/text patterns) or via a manual bank selector if
  auto-detection is ambiguous or fails.
- FR-3: If a PDF is scanned/image-based (no extractable text layer), the tool must detect
  this and clearly reject the file with an explanation, rather than silently producing
  empty or garbage output.
- FR-4: If a PDF belongs to a bank/format the tool does not yet support, it must fail
  clearly and explicitly, naming the unsupported bank/format, rather than attempting a
  best-effort generic parse.

### 5.2 Parsing engine

- FR-5: Each supported bank has its own parsing logic tuned to that bank's specific layout
  (column positions, header/footer patterns, date format, multi-line description handling,
  thousands separators, credit/debit sign conventions, etc.).
- FR-6: The parser must correctly reconstruct transactions that span multiple lines in the
  PDF (e.g. a long description wrapping to a second line) into a single logical transaction
  row — it must not create a spurious extra row, and must not lose the wrapped text.
- FR-7: The parser must strip non-transaction content: page headers/footers, repeated
  column headers on each page, disclaimers, opening/closing balance summary blocks (unless
  explicitly required — see FR-11), and page numbers.
- FR-8: The parser must correctly distinguish debit amounts, credit amounts, and running
  balance for each transaction, even when a bank's PDF presents them ambiguously (e.g. a
  single "Amount" column with a separate Dr/Cr indicator).
- FR-9: Dates must be parsed and normalized to a single consistent format in the output,
  regardless of the source format used by each bank (e.g. `DD/MM/YYYY`, `DD-MON-YYYY`).
- FR-10: Numeric amounts must be normalized (thousands separators removed, consistent
  decimal handling) and output as actual numeric values in Excel — not text strings —
  so totals/formulas work directly on the output.
- FR-11: The tool should capture opening balance and closing balance for the statement
  period (as metadata or as marked rows) so the user can verify extraction completeness by
  checking that transactions reconcile to the closing balance.

### 5.3 Output (Excel)

- FR-12: Every transaction is written as its own row. No merging of multiple transactions
  into one row, and no splitting of one transaction across multiple rows.
- FR-13: Output columns are fixed and consistent across all banks, regardless of each
  source PDF's original column order or naming:

  | Column | Description |
  |---|---|
  | Date | Transaction date, normalized format |
  | Description | Full transaction narration/details (multi-line source text joined) |
  | Debit | Debit amount (numeric), blank if not a debit |
  | Credit | Credit amount (numeric), blank if not a credit |
  | Balance | Running balance after the transaction, as stated in the source PDF |

  *(This schema is the v1 default. See §9 Open Items — confirm final column set/order
  before build, and whether a "Bank Name" / "Account Number" / "Source File" column should
  be added for multi-statement runs.)*

- FR-14: When multiple PDFs are processed in one run, the tool must either produce one
  Excel file per PDF, or consolidate all transactions into a single Excel file with a
  column identifying the source statement/account — this behavior should be a user choice,
  not fixed.
- FR-15: The Excel output must open cleanly in Excel/Google Sheets with correct data types
  (dates as dates, numbers as numbers) — not everything as text.

### 5.4 Validation & error handling

- FR-16: After parsing, the tool should validate internal consistency where possible —
  e.g., opening balance + sum(credits) − sum(debits) = closing balance — and warn the user
  if the reconciliation fails, since that likely indicates a missed or misparsed row.
- FR-17: If any page or section of the PDF could not be parsed, the tool must report this
  explicitly (which page, why) rather than silently omitting transactions.
- FR-18: The tool must never silently produce a partially-correct file without indicating
  that something went wrong.

---

## 6. Non-Functional Requirements

- NFR-1: **Accuracy over automation.** It is better for the tool to stop and flag a
  statement it's unsure about than to guess and produce a wrong value in the Excel file.
  This is a financial record — silent errors are the primary risk to avoid.
- NFR-2: **Local/offline processing.** Since these are personal bank statements, PDFs and
  extracted data should be processed entirely on the local machine — no upload to
  third-party services — for privacy.
- NFR-3: **Usability.** The desktop UI should let a non-technical user process a statement
  in a few clicks: select file(s) → confirm/select bank → export Excel. No manual
  configuration required for supported banks.
- NFR-4: **Maintainability/extensibility.** Adding support for a new bank format should be a
  contained, well-isolated change (e.g. a new parser module) that doesn't risk breaking
  existing supported banks.
- NFR-5: **Performance.** A typical monthly statement (tens to low hundreds of transactions,
  a few pages) should process in a few seconds.

---

## 7. Supported Banks (v1 scope)

To be finalized before development starts. For each bank, we need a sample (real or
redacted) statement PDF to build and test the parser against.

| # | Bank | Sample PDF available? | Notes |
|---|---|---|---|
| 1 | *(TBD)* | | |
| 2 | *(TBD)* | | |
| 3 | *(TBD)* | | |

> Each bank effectively requires its own mini-parser due to layout differences, so the
> list above directly drives development effort. Recommend starting with the 2-3 banks
> the user actually has statements from, then expanding.

---

## 8. Assumptions & Constraints

- Input PDFs are text-based/digitally generated (selectable text), not scanned images.
  Scanned statements are explicitly out of scope for v1 (would require OCR, a different
  and less reliable extraction approach).
- Statement layout for a given bank is reasonably stable over time (banks don't redesign
  statement formats often); if a bank changes its format, the corresponding parser will
  need updating.
- The user has legal access to and ownership of the statements being processed (these are
  the user's own accounts).
- One currency/locale (assumed INR/Indian number and date formatting conventions) unless
  stated otherwise — confirm if any statements use different conventions.

---

## 9. Open Items (need decisions before/at build start)

1. **Final Excel column set** — confirm the 5-column schema in FR-13, or extend it (e.g.
   add Bank Name, Account Number, Transaction Type/Reference No., Source File).
2. **Bank list** — which specific banks (and how many statement samples per bank) are in
   v1 scope (§7).
3. **Multi-file behavior** — one output file per PDF vs. consolidated workbook (FR-14).
4. ~~**Platform** — target OS for the desktop app and preferred tech stack.~~ **Decided:**
   Next.js frontend + Python/FastAPI backend + PostgreSQL, run locally via `docker-compose`
   (browser-based UI at `localhost`, not a native desktop app). See
   [architecture.md](./architecture.md).
5. **Naming convention** for output files (e.g. `<Bank>_<AccountLast4>_<StatementMonth>.xlsx`).

---

## 10. Success Criteria

The tool is considered successful for v1 if, for each supported bank:

- 100% of transactions in a test set of real statements are extracted, with zero missed
  or duplicated rows.
- Extracted values (date, description, debit, credit, balance) match the source PDF exactly
  for every transaction in the test set.
- The reconciliation check (opening balance → closing balance) passes for every test
  statement.
- The user can go from "PDF in hand" to "Excel file produced" without manual data cleanup.

---

## 11. Future Enhancements (explicitly out of scope for v1)

- OCR support for scanned statements.
- Automatic transaction categorization/tagging.
- A "generic mode" best-effort parser for banks without a dedicated parser.
- Web/cloud version with multi-user support.
- Direct integration with budgeting tools (e.g. export to YNAB, Google Sheets sync).
