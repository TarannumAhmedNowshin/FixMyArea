# FixMyArea --- Complete Project Flow & System Architecture

## 1. What is FixMyArea?

FixMyArea is a simple civic-assistance application.

A resident sees a public-space problem, uploads a photo and selects the
location. The system uses AI to understand the problem and Irish public
data to determine the correct next action.

> **We're helping Dublin residents turn everyday public-space problems
> into the right next action, using AI, location, and Irish
> local-government open data.**

The basic journey is:

**See → Capture → Understand → Locate → Route → Act**

------------------------------------------------------------------------

# 2. The Complete System Flow

``` text
                    USER
                     |
                     | sees a problem
                     v
             +------------------+
             |    FixMyArea     |
             |                  |
             |  Upload Photo    |
             |  Select Location |
             +--------+---------+
                      |
                      v
             +------------------+
             |    AI VISION     |
             |                  |
             | What is in the   |
             | photo?           |
             +--------+---------+
                      |
                      v
                CLASSIFY ISSUE
                      |
         +------------+-------------+
         |            |             |
         v            v             v
    Streetlight    Dumping       E-Waste
         |            |             |
         v            v             v
    Streetlight    Authority     Recycling
      Dataset       Dataset        Dataset
         |            |             |
         +------------+-------------+
                      |
                      v
                 USER LOCATION
                      |
                      v
             FIND CORRECT RESULT
                      |
                      v
             +------------------+
             |    FixMyArea     |
             | Recommendation   |
             +--------+---------+
                      |
                      v
                 NEXT ACTION
                      |
            +---------+---------+
            |                   |
            v                   v
       Prepare report       Find correct
       for service          disposal place
```

------------------------------------------------------------------------

# 3. What Does the User Do?

The citizen should have an extremely simple experience.

The first screen can contain:

``` text
+-----------------------------------+
|                                   |
|            FIX MY AREA            |
|                                   |
|   See a problem in your area?     |
|                                   |
|       [ Upload Photo ]            |
|                                   |
|       Select Location             |
|                                   |
|          [ ANALYSE ]              |
|                                   |
+-----------------------------------+
```

The user only needs to provide:

1.  A photograph.
2.  A location.

Everything else happens behind the scenes.

------------------------------------------------------------------------

# 4. Example 1 --- Broken Streetlight

Imagine someone sees a broken streetlight.

They open FixMyArea and upload a photograph.

## Step 1 --- AI understands the photograph

The photograph is sent to an AI model.

We ask the model to classify the image into a small set of categories:

``` text
street_light
illegal_dumping
electronic_waste
other
```

Example AI response:

``` json
{
  "category": "street_light",
  "confidence": 0.94,
  "description": "Possible damaged or non-operational streetlight"
}
```

The AI's job is only:

> **What am I looking at?**

The AI should NOT decide which council or government service is
responsible.

------------------------------------------------------------------------

# 5. Step 2 --- Get the Location

The user selects their location on a map or allows the application to
use their location.

Example:

``` text
Latitude:  53.34
Longitude: -6.27
```

Every location can be represented using latitude and longitude.

Now FixMyArea knows:

``` text
WHAT?
Broken streetlight

WHERE?
53.34, -6.27
```

------------------------------------------------------------------------

# 6. Step 3 --- Find the Responsible Local Authority

We use the Local Authority Boundaries dataset.

The backend asks:

``` text
Which local-authority polygon contains:

53.34, -6.27?
```

The result might be:

``` text
Dublin City Council
```

Now we know which authority covers the selected location.

------------------------------------------------------------------------

# 7. Step 4 --- Find the Actual Streetlight

Next, we use the Dublin City Council Public Lighting dataset.

A simplified version might look like:

  Asset         Latitude   Longitude
  ----------- ---------- -----------
  Light 101      53.3401     -6.2702
  Light 102      53.3410     -6.2721
  Light 103      53.3440     -6.2801

Our Python backend calculates which streetlight is closest to the user's
selected location.

Example:

``` text
User location
     |
     | 12 metres
     |
Streetlight 101
```

The application can then show:

``` text
Nearest identified public-lighting asset:

Asset: Light 101
Distance: approximately 12 metres
Authority: Dublin City Council
```

This makes the report more useful than simply saying:

> "There is a broken streetlight somewhere on this road."

------------------------------------------------------------------------

# 8. Step 5 --- Routing Rules

Now the system knows:

``` text
Problem:
Streetlight

Location:
53.34, -6.27

Authority:
Dublin City Council

Nearest asset:
Light 101
```

We maintain a small routing file:

``` text
routing_rules.json
```

Conceptually it contains:

  Problem            Next Action
  ------------------ -----------------------------
  Streetlight        Public-lighting reporting
  Illegal dumping    Waste/environment reporting
  Electronic waste   Recycling facility lookup
  Pothole            Roads reporting

This file contains verified routing information.

The LLM should not invent government destinations.

------------------------------------------------------------------------

# 9. Step 6 --- Generate the Report

Once all the factual information is available, AI can help create a
clean description.

Example:

``` text
BROKEN STREETLIGHT REPORT

Issue:
Possible broken streetlight

Location:
Thomas Street, Dublin

Nearest identified asset:
Light 101

Distance:
12 metres

Description:
A streetlight near the selected location appears to
be damaged or non-operational based on the submitted
photograph.

Evidence:
1 photograph attached
```

The citizen can copy this report or continue to the official reporting
service.

------------------------------------------------------------------------

# 10. Final Streetlight Screen

``` text
+------------------------------------+
|                                    |
|       STREETLIGHT ISSUE            |
|                                    |
| Dublin City Council                |
|                                    |
| Nearest lighting asset:            |
| Light 101                          |
|                                    |
| Distance: 12 metres                |
|                                    |
| Your report is ready.              |
|                                    |
|       [ COPY REPORT ]              |
|                                    |
|       [ REPORT ISSUE ]             |
|                                    |
+------------------------------------+
```

That completes one full FixMyArea journey.

------------------------------------------------------------------------

# 11. Example 2 --- Electronic Waste

Suppose someone uploads a photograph of a broken laptop.

The first part is identical:

``` text
Photo
  |
  v
AI
```

But the AI now returns:

``` text
electronic_waste
```

The system does NOT query the streetlight dataset.

Instead:

``` text
Broken Laptop
      |
      v
     AI
      |
      v
Electronic Waste
      |
      v
User Location
      |
      v
Recycling Dataset
      |
      v
Find nearby appropriate facility
      |
      v
Disposal / recycling instructions
```

The final result could look like:

``` text
ELECTRONIC WASTE

This item should not be placed in general waste.

Nearby recycling option:

[Facility Name]
[Address]

Distance:
1.8 km

[ GET DIRECTIONS ]
```

The important idea is that FixMyArea chooses the appropriate data source
based on what the AI identifies.

------------------------------------------------------------------------

# 12. Example 3 --- Illegal Dumping

Suppose someone photographs a dumped mattress.

The flow becomes:

``` text
Photo of mattress
       |
       v
      AI
       |
       v
Illegal Dumping
       |
       v
User Location
       |
       v
Local Authority Dataset
       |
       v
Responsible Council
       |
       v
Routing Rules
       |
       v
Waste / Dumping Reporting
       |
       v
Generate Description
       |
       v
Report Ready
```

Example output:

``` text
ILLEGAL DUMPING

Authority:
Dublin City Council

Location:
[Selected Location]

Description:
A mattress appears to have been dumped at the
selected public location.

Evidence:
1 photograph

[ COPY REPORT ]

[ CONTINUE TO OFFICIAL SERVICE ]
```

------------------------------------------------------------------------

# 13. All Three Flows Together

``` text
                       PHOTO
                         |
                         v
                        AI
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
     STREETLIGHT      DUMPING        E-WASTE
          |              |              |
          v              v              v
       Location       Location       Location
          |              |              |
          v              v              v
    Streetlight       Authority      Recycling
      Dataset          Dataset        Dataset
          |              |              |
          v              v              v
    Nearest Light    Correct Council Nearest Centre
          |              |              |
          v              v              v
    Prepare Report   Prepare Report Disposal Advice
          |              |              |
          v              v              v
      REPORT IT       REPORT IT       RECYCLE IT
```

------------------------------------------------------------------------

# 14. Why We Use Multiple Datasets

We do NOT need to merge every dataset into one giant file.

Different problems require different information.

Example:

``` text
Streetlight problem
       |
       +--> Local Authority dataset
       |
       +--> Public Lighting dataset
```

Electronic waste:

``` text
Electronic waste
       |
       +--> Recycling dataset
```

Illegal dumping:

``` text
Illegal dumping
       |
       +--> Local Authority dataset
       |
       +--> Routing rules
```

The datasets are dynamically connected depending on the user's problem.

------------------------------------------------------------------------

# 15. System Architecture

The application has four main components.

``` text
+------------------------------------------------+
|                    WEBSITE                     |
|                    Next.js                     |
|                                                |
| Upload Photo | Select Location | Show Result   |
+-----------------------+------------------------+
                        |
                        v
+------------------------------------------------+
|                    BACKEND                     |
|               Python + FastAPI                 |
|                                                |
| Controls the application flow                  |
+---------+----------------+----------------+----+
          |                |                |
          v                v                v
       OpenAI          Government        Routing
         AI               Data            Rules
          |                |                |
          v                v                v
     Understand       Find location       Decide
       photo          / asset/facility  next action
```

------------------------------------------------------------------------

# 16. Frontend

The frontend is simply the website the citizen sees.

Recommended technology:

``` text
Next.js
```

Its responsibilities are:

-   upload photograph;
-   show/select location;
-   send information to backend;
-   show analysis result;
-   show asset/facility;
-   display final action;
-   provide report/directions button.

The frontend should NOT contain complicated data-processing logic.

------------------------------------------------------------------------

# 17. Backend

The backend is the brain of FixMyArea.

Recommended technology:

``` text
Python + FastAPI
```

It receives:

``` text
Photo
Location
Optional description
```

Then performs:

``` text
1. Ask AI what the photo contains.

2. Determine which dataset is required.

3. Query the appropriate public dataset.

4. Determine the responsible authority/service.

5. Apply routing rules.

6. Generate a useful response.

7. Return everything to the frontend.
```

------------------------------------------------------------------------

# 18. AI Component

We do NOT train our own machine-learning model.

Use a multimodal AI model to classify the photograph.

Its main responsibility:

> **What is this problem?**

Example output:

``` json
{
  "category": "illegal_dumping",
  "confidence": 0.91,
  "description": "A mattress appears to have been dumped beside a public road."
}
```

Keep the allowed categories small.

For the POC:

``` text
street_light
illegal_dumping
electronic_waste
other
```

------------------------------------------------------------------------

# 19. Government Data Component

Government/public data answers:

> **What exists here?**

and:

> **Which authority/service is relevant?**

Initial datasets:

``` text
Public Lighting dataset
        +
Local Authority Boundaries
        +
Recycling Centres
```

The system selects whichever dataset is relevant to the identified
problem.

------------------------------------------------------------------------

# 20. Do We Need a Database?

Not initially.

For the hackathon POC, the datasets can simply be stored as files.

Example project:

``` text
fixmyarea/

    data/
        streetlights.csv
        recycling_centres.csv
        local_authorities.geojson

    backend/

    frontend/
```

Python can load these files directly.

Avoid adding unnecessary infrastructure such as:

-   PostgreSQL
-   Redis
-   AWS
-   Kubernetes
-   complicated authentication

unless the basic product is already working.

------------------------------------------------------------------------

# 21. Suggested Project Structure

Eventually the project can look approximately like this:

``` text
fixmyarea/

|
+-- frontend/
|     |
|     +-- FixMyArea website
|
+-- backend/
|     |
|     +-- main.py
|     +-- ai.py
|     +-- location.py
|     +-- routing.py
|
+-- data/
|     |
|     +-- streetlights.csv
|     +-- local_authorities.geojson
|     +-- recycling_centres.csv
|
+-- routing_rules.json
```

### What each file does

`main.py`

Receives requests from the website and coordinates everything.

`ai.py`

Sends the photograph to the AI and receives the issue category.

`location.py`

Handles geographic calculations such as nearest streetlight, authority,
or recycling facility.

`routing.py`

Decides what action should happen for each category.

`routing_rules.json`

Stores verified mappings between problem types and official
destinations/actions.

------------------------------------------------------------------------

# 22. How the Frontend and Backend Communicate

The website sends something conceptually like:

``` json
{
  "photo": "uploaded_photo",
  "latitude": 53.34,
  "longitude": -6.27
}
```

to:

``` text
POST /api/analyse
```

The backend returns:

``` json
{
  "category": "street_light",
  "authority": "Dublin City Council",
  "nearest_asset": "Light 101",
  "distance_m": 12,
  "next_action": "report",
  "description": "Possible broken streetlight"
}
```

The frontend converts this response into the nice result screen.

------------------------------------------------------------------------

# 23. Build the Project Backwards From the Demo

Because this is a hackathon and the team is new to coding, do NOT build
every component simultaneously.

Build one small flow first.

## Stage 1

``` text
Location
   |
   v
Streetlight CSV
   |
   v
Find nearest streetlight
   |
   v
Display result
```

If this works, your first public-data integration works.

------------------------------------------------------------------------

## Stage 2

Add AI:

``` text
Photo
   |
   v
AI
   |
   v
Streetlight
   |
   v
Location
   |
   v
Dataset
   |
   v
Nearest streetlight
```

------------------------------------------------------------------------

## Stage 3

Add the useful action:

``` text
Photo
   |
   v
AI
   |
   v
Streetlight
   |
   v
Location
   |
   v
Government Dataset
   |
   v
Nearest Streetlight
   |
   v
Authority
   |
   v
Generate Report
   |
   v
REPORT ISSUE
```

At this point you have a legitimate POC.

------------------------------------------------------------------------

# 24. Only Then Add the Other Categories

Once the streetlight flow works:

### Add illegal dumping

``` text
Photo
 -> AI
 -> Illegal Dumping
 -> Location
 -> Local Authority
 -> Report
```

### Then add electronic waste

``` text
Photo
 -> AI
 -> Electronic Waste
 -> Location
 -> Recycling Dataset
 -> Nearest Facility
 -> Directions
```

Do not build all three at the same time.

------------------------------------------------------------------------

# 25. Development Priority

## P0 --- Must Work

1.  Upload photograph.
2.  Select/provide location.
3.  AI identifies one supported problem.
4.  Backend reads a real government dataset.
5.  Location lookup works.
6.  User receives a useful next action.

## P1 --- Should Work

7.  Three issue categories.
8.  Local-authority lookup.
9.  Nearest streetlight.
10. Nearest recycling facility.
11. Generated report.
12. Map.

## P2 --- Only If Time Remains

13. Duplicate issue detection.
14. More issue categories.
15. Database.
16. User accounts.
17. Advanced UI animations.
18. Nationwide support.

------------------------------------------------------------------------

# 26. The First Target

Before doing anything complicated, make this work:

``` text
INPUT

Latitude:
53.34

Longitude:
-6.27


        |
        v


STREETLIGHT DATASET


        |
        v


DISTANCE CALCULATION


        |
        v


OUTPUT

Nearest streetlight:
Asset XXXXX

Distance:
23 metres
```

Once this works, connect the AI.

------------------------------------------------------------------------

# 27. What Not to Do

Because the team has limited hackathon time, avoid:

``` text
Building a mobile app
        X

Training an ML model
        X

Building authentication
        X

Setting up AWS
        X

Building a huge database
        X

Supporting every Irish council
        X

Building 20 issue categories
        X

Making a giant dashboard
        X
```

None of these are required to prove the concept.

------------------------------------------------------------------------

# 28. What the Judges Should See

The strongest demonstration is:

``` text
User uploads photograph
          |
          v
AI identifies problem
          |
          v
Location is selected
          |
          v
Real public dataset queried
          |
          v
Real asset/service/facility identified
          |
          v
FixMyArea explains what to do
          |
          v
Citizen takes action
```

The important part is that government data is actually being used inside
the product rather than merely visualised.

------------------------------------------------------------------------

# 29. 60--90 Second Demo Story

Start with:

> "People shouldn't need to understand council structures just to report
> a broken streetlight or figure out what to do with a discarded item."

Then demonstrate:

``` text
Upload streetlight photo
        |
        v
AI: Streetlight issue
        |
        v
Select location
        |
        v
Government dataset lookup
        |
        v
Nearest lighting asset
        |
        v
Dublin City Council
        |
        v
Report generated
```

Then upload a photograph of a laptop.

The system changes workflow:

``` text
Laptop
   |
   v
Electronic Waste
   |
   v
Recycling Dataset
   |
   v
Nearby appropriate destination
```

This shows that FixMyArea is not simply an image classifier.

It is a **civic routing system**.

------------------------------------------------------------------------

# 30. Core Technical Message

The architecture can be explained in one sentence:

> **AI understands the problem, public data understands the place and
> available services, and FixMyArea combines them to determine the
> citizen's next action.**

Or even shorter:

``` text
AI       = WHAT?
Location = WHERE?
Data     = WHAT EXISTS THERE?
Rules    = WHO / WHERE SHOULD IT GO?
FixMyArea = WHAT SHOULD I DO NEXT?
```

------------------------------------------------------------------------

# 31. Definition of Done

The POC is complete when a user can:

1.  Upload a photograph.
2.  Select the problem location.
3.  Have AI identify the problem.
4.  See information obtained from a real public dataset.
5.  See the relevant authority, asset, or facility.
6.  Receive a clear next action.

If only the streetlight flow works perfectly, that is better than having
ten incomplete features.

The product should leave the user thinking:

> **"I saw a problem, and now I know exactly what to do."**
