# FixMyArea --- 4-Hour POC Plan of Action

## 1. One useful thing

**Product sentence**

> **We're helping Dublin residents turn everyday public-space problems
> into the right next action, using AI, location, and Irish
> local-government open data.**

**Core user flow**

**See → Capture → Understand → Locate → Route → Act**

A resident takes a photo or describes a problem. FixMyArea identifies
the issue, uses the location and public datasets to determine the
relevant asset/authority/service, prepares a useful report or disposal
instruction, and sends the user to the right next step.

------------------------------------------------------------------------

## 2. Lock the POC scope before coding

Do **not** try to support every possible council issue.

### MVP scenarios

1.  **Broken streetlight**
    -   Detect a streetlight-related issue.
    -   Capture/select location.
    -   Find the nearest public-lighting asset where data is available.
    -   Determine the responsible local authority.
    -   Prepare a report.
2.  **Illegal dumping**
    -   Detect dumped rubbish/waste.
    -   Capture/select location.
    -   Determine the local authority.
    -   Prepare a report and route the user to the appropriate reporting
        service.
3.  **Electronic/recyclable item**
    -   Detect an item such as a laptop or small electrical appliance.
    -   Explain that it is a disposal/recycling problem rather than a
        street defect.
    -   Find an appropriate nearby recycling/civic-amenity destination
        from public data.

### Do not build in the MVP

-   User accounts
-   Authentication
-   Payments
-   A full council case-management system
-   Automatic submission into council systems unless an official API is
    available
-   A custom ML model
-   Nationwide support
-   Complex computer vision
-   Native mobile app

**Target:** one polished Dublin flow that genuinely works.

------------------------------------------------------------------------

# 3. Data first

## Dataset A --- Public lighting

**Purpose:** match a reported broken streetlight to a real
public-lighting asset.

Look for:

-   latitude
-   longitude
-   asset/unit identifier
-   road/location
-   any asset metadata available

Preferred format: **GeoJSON or CSV**

Initial task:

1.  Download dataset.
2.  Load into Python/Pandas or GeoPandas.
3.  Confirm coordinates are usable.
4.  Plot 10--20 points on a map.
5.  Write a function:

`find_nearest_streetlight(latitude, longitude)`

Expected output:

``` json
{
  "asset_id": "...",
  "distance_m": 18,
  "latitude": 53.34,
  "longitude": -6.27
}
```

------------------------------------------------------------------------

## Dataset B --- Local-authority boundaries

**Purpose:** determine which local authority is responsible for the
reported location.

Required fields:

-   authority name
-   polygon/multipolygon geometry

Function:

`find_local_authority(latitude, longitude)`

Example:

``` json
{
  "authority": "Dublin City Council"
}
```

Use point-in-polygon lookup.

For the POC, if geospatial setup starts consuming time, support **Dublin
City Council only** and clearly label the prototype accordingly.

------------------------------------------------------------------------

## Dataset C --- Recycling / civic amenity facilities

**Purpose:** route recyclable/electrical items to a useful destination.

Useful fields:

-   facility name
-   latitude
-   longitude
-   address
-   accepted materials if available
-   opening/service information if available

Function:

`find_nearby_facilities(latitude, longitude, item_type)`

Return the nearest suitable options.

------------------------------------------------------------------------

## Dataset D --- Reporting destinations / service directory

This can initially be a **small curated routing table** rather than
another large dataset.

Example:

  Issue category    Destination
  ----------------- -------------------------------------------
  street_light      Public lighting / council reporting route
  pothole           Roads / council reporting route
  illegal_dumping   Waste / environmental reporting route
  graffiti          Public realm / council reporting route
  ewaste            Recycling facility lookup

Store it as `routing_rules.json`.

The important thing is that the AI does **not invent** the destination.
Routing should come from verified rules/data.

------------------------------------------------------------------------

# 4. Technical architecture

Keep the stack extremely small.

``` text
Next.js frontend
      |
      | photo + description + location
      v
FastAPI backend
      |
      +---- OpenAI Vision / multimodal model
      |       |
      |       +--> issue classification
      |
      +---- Geospatial service
      |       |
      |       +--> nearest streetlight
      |       +--> local authority
      |       +--> nearest recycling facility
      |
      +---- Routing rules
      |
      +---- OpenAI text generation
              |
              +--> clean report description

      v
Structured result
      |
      v
Citizen action screen
```

### Suggested stack

-   **Frontend:** Next.js
-   **Backend:** FastAPI
-   **Data:** Pandas/GeoPandas or lightweight in-memory JSON/GeoJSON
-   **Map:** Leaflet / React Leaflet
-   **AI:** OpenAI multimodal model
-   **Prototype storage:** SQLite or even JSON; only add persistence if
    needed

Do not introduce Redis/Postgres/Docker unless already set up and
effortless.

------------------------------------------------------------------------

# 5. Define the API contract before building UI

## `POST /api/analyse`

Input:

``` json
{
  "image": "<uploaded image>",
  "description": "optional user description",
  "latitude": 53.34,
  "longitude": -6.27
}
```

Output:

``` json
{
  "category": "street_light",
  "label": "Possible broken streetlight",
  "confidence": 0.93,
  "authority": "Dublin City Council",
  "asset": {
    "id": "LIGHT-1234",
    "distance_m": 14
  },
  "next_action": "report",
  "destination": {
    "name": "Public Lighting",
    "official_url": "VERIFIED_OFFICIAL_DESTINATION"
  },
  "draft_report": {
    "title": "Streetlight issue",
    "description": "A streetlight at the selected location appears..."
  }
}
```

Use the same endpoint for all three scenarios.

------------------------------------------------------------------------

# 6. AI classification

Give the model a **closed set of categories**.

For the POC:

``` text
street_light
illegal_dumping
electronic_waste
other
```

Ask for structured JSON only.

The model should identify:

-   category
-   short human-readable label
-   confidence
-   visible evidence
-   whether more information is required

Do not let the LLM decide the council/service from memory.

**AI = understand the problem.**

**Public data/rules = decide where it goes.**

That separation is important.

------------------------------------------------------------------------

# 7. Build the prototype in this order

## Phase 1 --- 0:00--0:30

### Validate the data

Owner: Data/backend person

-   Download the three essential datasets.
-   Check coordinate systems.
-   Verify at least one streetlight lookup.
-   Verify one authority lookup.
-   Verify one recycling-facility lookup.
-   Create a tiny cleaned dataset if the originals are huge.

**Exit condition:** Given a latitude/longitude, Python can return useful
government-data results.

Do not build UI until this works.

------------------------------------------------------------------------

## Phase 2 --- 0:30--1:00

### Build the thinnest end-to-end prototype

Ignore AI temporarily.

Hard-code:

``` text
category = street_light
```

Build:

`frontend → FastAPI → dataset lookup → JSON response`

The page needs only:

-   image upload
-   location / map pin
-   Analyse button
-   result card

**Exit condition:** clicking Analyse produces a real
streetlight/local-authority result.

This proves the architecture.

------------------------------------------------------------------------

## Phase 3 --- 1:00--1:40

### Add AI image understanding

Connect the uploaded image to OpenAI.

Output one of:

``` text
street_light
illegal_dumping
electronic_waste
other
```

Test with at least:

-   streetlight photo
-   dumped mattress/rubbish photo
-   laptop/electronic item photo

**Exit condition:** all three demo scenarios route to different backend
logic.

------------------------------------------------------------------------

## Phase 4 --- 1:40--2:20

### Build the routing engine

Pseudo-logic:

``` python
if category == "street_light":
    authority = find_local_authority(location)
    asset = find_nearest_streetlight(location)
    action = "report"

elif category == "illegal_dumping":
    authority = find_local_authority(location)
    action = "report"

elif category == "electronic_waste":
    facilities = find_nearby_facilities(location)
    action = "recycle"
```

Keep this deterministic.

Do not ask the LLM to invent routing.

------------------------------------------------------------------------

## Phase 5 --- 2:20--2:50

### Generate the useful action

For reportable issues, generate a concise draft:

``` text
Issue
Broken streetlight

Location
[location]

Nearest identified asset
[asset]

Description
A public streetlight at the selected location appears
to be non-operational/damaged based on the submitted
photo.

Evidence
1 photograph
```

For disposal:

``` text
Item
Electronic equipment

Recommended action
Use an appropriate WEEE/recycling facility.

Nearby option
[facility]
[address]
[distance]

[Get directions]
```

**Exit condition:** the citizen knows exactly what to do next.

------------------------------------------------------------------------

## Phase 6 --- 2:50--3:20

### Make the map useful

Show:

-   user's selected location
-   nearest asset or facility
-   authority/service
-   distance

Do not spend time building a giant city-wide dashboard.

The map exists to support the **individual action**.

------------------------------------------------------------------------

## Phase 7 --- 3:20--3:40

### Add one memorable feature

Only if the main flow works.

Best option:

### Duplicate issue detection

Store prototype reports:

``` text
category
latitude
longitude
timestamp
```

Before creating a new report, check for a nearby report of the same
category.

Example:

> **This issue may already have been reported nearby.**
>
> 8 people have flagged a similar streetlight issue here.
>
> **\[Same issue\]**

For the hackathon this can use SQLite or an in-memory/JSON store.

If this risks the demo, skip it.

------------------------------------------------------------------------

# 8. Final UI

## Screen 1

``` text
FIXMYAREA

See something that needs attention?

[ Take / upload photo ]

or

[ Describe the problem ]

📍 Use my location / Select on map

             [ Analyse ]
```

## Screen 2

``` text
Possible broken streetlight

[photo]

📍 Selected location
🏛 Dublin City Council

Nearest lighting asset
Asset XXXXX — 14m away

We've prepared the next step.

            [ Continue ]
```

## Screen 3

``` text
READY TO REPORT

Issue
Streetlight fault

Location
...

Asset
...

Description
...

[ Copy report ]

[ Continue to official service ]
```

For recycling, Screen 3 becomes:

``` text
THIS ITEM NEEDS A DIFFERENT DESTINATION

Electronic equipment

Nearest suitable facility
...

1.6 km away

[ Directions ]
```

------------------------------------------------------------------------

# 9. Testing checklist

Before adding anything else, test these three flows from beginning to
end.

### Test A --- streetlight

`photo → classify → locate → asset → authority → report`

### Test B --- illegal dumping

`photo → classify → locate → authority → report`

### Test C --- electronic item

`photo → classify → locate → recycling destination`

Also test:

-   AI cannot classify image.
-   GPS/location missing.
-   No nearby asset found.
-   Location outside supported area.
-   Dataset lookup fails.

The application should fail gracefully rather than hallucinating an
answer.

------------------------------------------------------------------------

# 10. Demo script

Keep the live demo around **60--90 seconds**.

### Opening

> "People shouldn't need to understand council structures just to report
> a broken streetlight or figure out what to do with a discarded item."

### Demo 1

Upload a broken-streetlight image.

FixMyArea:

1.  identifies the issue;
2.  uses the selected location;
3.  finds the relevant public-lighting asset;
4.  identifies the responsible authority;
5.  prepares the report;
6.  provides the verified next action.

### Demo 2

Upload a laptop/electrical-item image.

FixMyArea recognises that this is **not the same workflow**.

It finds an appropriate recycling destination instead.

### Closing

> **"The AI understands what you're looking at. Public data understands
> where you are and what services exist. FixMyArea combines both to
> answer one useful question: what should I do next?"**

------------------------------------------------------------------------

# 11. Team split

If there are four people:

### Person 1 --- Data

-   download/clean datasets
-   geospatial lookup functions
-   verify government sources

### Person 2 --- Backend

-   FastAPI
-   AI classification
-   routing engine
-   report generation

### Person 3 --- Frontend

-   image upload
-   map/location
-   results/action screens

### Person 4 --- Product/demo

-   verify official destinations
-   test flows
-   edge cases
-   slides/demo story
-   prepare backup screenshots/video

If there are fewer people, combine Data + Backend first. The polished UI
comes after the end-to-end path works.

------------------------------------------------------------------------

# 12. Priority order if time starts disappearing

Build in this exact order:

**P0** 1. One real dataset connected. 2. Photo upload. 3. AI
classification. 4. Location. 5. Correct deterministic routing. 6. Useful
final action.

**P1** 7. All three categories. 8. Map. 9. AI-generated report.

**P2** 10. Duplicate reports. 11. Additional issue types. 12. Better
animations/design.

If only **one scenario** works perfectly after three hours, polish that
scenario rather than building five broken ones.

------------------------------------------------------------------------

# 13. Definition of done

The POC is successful if someone who has never seen the project can:

1.  upload a photo;
2.  select where the problem is;
3.  understand what FixMyArea thinks the problem is;
4.  see real information retrieved from public data;
5.  understand which service/destination is relevant;
6.  leave with a concrete next action.

That is the product.

**Not:** "Look at all the data we visualised."

**But:** "I had a real-world problem, and now I know exactly what to
do."
