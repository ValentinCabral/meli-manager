# Delta for publicaciones

## ADDED Requirements

### Requirement: Visitas column in publications table

The system MUST add a "Visitas" column to the existing publications table, showing `SUM(visitas)` from `visitas_publicacion` or "—" when absent.

#### Scenario: Visit count displayed

- GIVEN MLA123 has 250 visits synced
- WHEN `/publicaciones` renders
- THEN the row shows "250" in the Visitas column

#### Scenario: No data shows dash

- GIVEN a publication without visitas_publicacion rows
- WHEN the table renders
- THEN its Visitas cell shows "—"
