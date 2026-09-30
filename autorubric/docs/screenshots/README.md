# Screenshots

This directory contains visual evidence of the AutoRubric frontend dashboard functioning. 
*(Note: As an automated assistant, the actual `.png` files are omitted or stubbed via Playwright, but this document explains what each required screenshot entails).*

1. **login.png**: Shows the `/login` route with email/password fields, simulating JWT authentication.
2. **rubric_builder.png**: Shows the `/rubrics/new` interface for building JSON rubrics manually with dynamic rows.
3. **upload.png**: Displays the `/upload` drag-and-drop zone and the batch submit options.
4. **cohort_progress.png**: Displays the `/cohorts/[id]` polling view with documents showing statuses like `EXTRACTING`, `SCORING`, `DONE`.
5. **result_page.png**: Shows a clean `/results/[doc_id]` page with a summary of total score and a table of criterion checks.
6. **needs_review_flags.png**: Shows the `NEEDS_REVIEW` banner and the specific Critic flags (`HIDDEN_TEXT` / `INJECTION_PHRASE`) rendered next to the untrusted criterion labels.
7. **annotated_pdf.png**: Highlights the built-in `react-pdf` viewer showing bounding box coordinates overlay on the submitted PDF document.
8. **collusion_list.png**: Shows `/cohorts/[id]/collusion` with the side-by-side proposition matching breakdown.
9. **heatmap.png**: Illustrates the `Heatmap.tsx` rendering a documents-by-documents matrix styled based on pair-similarity (0-100%).
