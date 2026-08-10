# Forslag til ny datafangst for WorkOp

## Hvorfor

Én Excel-fil med ett ark per WorkOp skalerer ikke til 171+ arrangementer/år fra 2027.
Inkonsistent formatering gir mye manuell kode. Ingen skille mellom data fra arrangementsdagen
og ansettelsesdata 4 uker etterpå.

## Løsning: 2 MS Forms → SharePoint-Excel

Koordinator fyller ut to skjemaer per WorkOp. Svar lagres automatisk i Excel på SharePoint.

| Skjema | Tidspunkt | Innhold |
|--------|-----------|---------|
| **Gjennomføring** | Rett etter WorkOp | Oppmøte, arbeidsgivere, speedintervjuer |
| **Oppfølging** | ~4 uker etter | Ansettelser, innsatsgrupper |

Ved behov: migrer til SharePoint-liste via Power Automate for bedre validering og Graph API.

---

## Skjema 1 — Gjennomføring

| Felt | Type |
|------|------|
| Dato | Dato ✱ |
| Nav-kontor | Nedtrekksliste ✱ (liste over aktuelle kontorer) |
| Oppmøtte — forberedende workshop | Tall |
| Oppmøtte — selve WorkOp | Tall ✱ |
| Innkalt til intervju | Tall |

**Få med noe om bistandsbehovet til deltakerne på workop**
^ønsker å belyse at de som møter opp er i ungdomsgarantien (dvs trenger bistand og nedsatt arb.evne).

**Arbeidsgivere** — 10 faste slots i samme skjema. Tomme slots ignoreres.
Maks i data hittil er 10, snitt 5,4 — utvid ved behov.

| Felt per arbeidsgiver | Type |
|-----------------------|------|
| Bedriftsnavn | Tekst |
| Bransje | Nedtrekksliste (se under) |
| Antall ansatte | Tall |
| Rekrutteringsbehov | Tall |
| Antall speedintervjuer | Tall |

Ved innsending genereres en **WorkOp-ID** automatisk (`BÆRUM-2027-03-21`).
Koordinator får IDen i kvitteringssiden og bruker den i Skjema 2.

---

## Skjema 2 — Oppfølging

| Felt | Type |
|------|------|
| WorkOp-ID | Nedtrekksliste ✱ (populert fra Skjema 1-svar) |
| Totalt fikk jobb | Tall ✱ |
| — herav med tiltak | Tall |
| — herav nedsatt arbeidsevne | Tall |
| — herav trenger veiledning | Tall |
| — herav gode muligheter | Tall |

**TODO: Få med: Hvor mange som fikk jobbtilbud, men takket nei**

**Per arbeidsgiver** — auto-populert fra Skjema 1 via WorkOp-ID:

| Felt | Type |
|------|------|
| Bedriftsnavn | Forhåndsutfylt |
| Aktuell for ordinær ansettelse | Tall |
| Faktisk ansatt | Tall |

#### TODO: Enten trenger vi å kunne oppdatere skjema 2 fordi noen får ny informasjon etter uke 5 og 6. Enten oppdatere skjema 2 eller et eventuelt skjema 3.

### Validering (i Forms eller ved innlesing)

- Sum innsatsgrupper ≤ totalt fikk jobb (i dag avviker 45 % av radene)
- Sum ansatt per arbeidsgiver ≤ totalt fikk jobb
- Oppmøtte ≥ innkalt ≥ fikk jobb

---

## Bransje-nedtrekksliste

Her er et forslag til bransjekategorier basert på dataen som er samlet inn så langt.
Lista kan med fordel justeres.

Varehandel og butikk · Restaurant og servering · Sikkerhet og vakt · Industri og produksjon · Renhold · Helse og omsorg · Bygg og anlegg · Hotell og reiseliv · Bil og kjøretøy · Barnehage og utdanning · Lager og logistikk · Annet

---
---
---

# Teknisk uthenting av data i etterkant

Forms-Excel leses via OneDrive-synk eller Graph API.
Arbeidsgiverdataen (10 faste slots) gir brede kolonner som reshapes til lang form:

```python
df = pd.read_excel("skjema1-svar.xlsx")
df_ag = pd.wide_to_long(df, stubnames=["ag_navn", "ag_bransje", ...], i="workop_id", j="ag_nr")
df = df.merge(pd.read_excel("skjema2-svar.xlsx"), on="workop_id", how="left")
```

Historiske data (WorkOp 1–56) blir i nåværende Excel-fil. Pipelinen leser begge kilder
og merger til felles format — `transform.py` og `plots.py` uendret.

## Migrasjon

1. Fortsett med Excel-fil resten av 2026
2. Sett opp Forms og test med 2–3 piloter
3. Legg til Forms-lesing i `extract.py`, behold Excel-lesing for historikk
4. Vurder SharePoint-liste hvis Excel ikke holder

## Åpne spørsmål

- [ ] Er det noe annen data som bør være med i første versjon av skjemaene?
- [ ] Skal dagsverk/kostnader med i nytt skjema, eller droppes?
- [ ] Er 4 uker etter WorkOp riktig tidspunkt?
- [ ] Bransjelista bør justeres basert på hva vi vil vite.
