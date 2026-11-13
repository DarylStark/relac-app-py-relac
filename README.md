# Relac

## Book ownership

Books can keep the existing list of owner IDs:

```yaml
owners:
  - owner.daryl
```

For ownership details, use an object with an `owner` ID. The optional `since`
date, `loans` history, and one optional `link` can be recorded for each owner.
Each loan records the borrower, loan date, due date, and optional return date.
Loans without a `returned_on` date are treated as active.
Active loan recipients contribute to the book's availability, while the
existing availability aggregation still gives precedence to a better status.

```yaml
owners:
  - owner: owner.daryl
    since: 2024-05-01
    loans:
      - loaned_to: owner.library
        loaned_on: 2026-01-02
        due_date: 2026-01-30
        returned_on: 2026-01-29
      - loaned_to: owner.example
        loaned_on: 2026-03-01
        due_date: 2026-03-15
    link:
      title: Loan record
      url: https://example.com/loan
```

The simple ID form remains supported and is treated as an ownership entry
without additional details. `loaned_to` is an owner ID and resolves to its
owner object when the database is resolved. For backwards compatibility, the
former `loaned_to`, `loaned_on`, and `due_date` fields are read as one active
loan.
