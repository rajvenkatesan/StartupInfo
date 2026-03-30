# Startup Info Discovery App

## Introduction
App that will dive deep and analyze company, investors, and the field they are in and then drill down on those investing companies to gather more companies to research on.

## Goal
A mobile app that users can use to get details of a company, their investors, investment details, etc. The application will drill down to each investor and identify additional startup companies they have invested in and add them to the app. Eventually, users will be able to search for jobs in these companies that suits their criteria (location, job type). This app will become a dictory for companies, investors, and jobs at these companies. User should be able to have an easy way of tracking which company, which job they have applied and when along with status etc. so that it becomes their key job search database.
 
## Spec
1. Front end will be a mobile app (IOS first)
2. Backend will have a database to store all this information in various tables
3. Add necessary logging and tracing when database is changed by the tool or by user.
4. All code should be stored in github and requires PR review
5. Add necessary tests before raising PR
6. Develop architecture doc, key stack technologies used, feature list, instructions for building and running the application. Keep the document updated with each change to make sure it is accurate.
7. When doing incremental development, match the existing code. If introducing new third party tool, get it reviewed before implementation.
8. Initially, I should be able to run it locally and then move the backend to some hosted cloud infrastructure with minimal cost and minimal redesign of the product.


## Spec Notes

1. When user specifies a company, analyze the company and find all its investors. Store the information in a investor table database with following fields (company name, investor name, series name, investor details, amount invested if known or -1 if not known, investor type (individual or company), additional comments column (such as lead VC), etc.
2. Use company name + investor name + series name as primary key and if that row
 is already present, update it. If same company has done multiple rounds, then it will be new row as series name will be different. 
3. Have a table of startup companies with following fields - company name, location, description, company type (public/private), about the company, vision, mission, founders.
4. Develop ios mobile app which will have a search function at the top. Given a company name, it will search company table and if found will return that row in a list view. From this company, user should be able to see all the information in the investor table. If company is not found, provide a "discover" button and onces pressed, will perform and delegate web search to look for the company details and populate company table and investor table.
5. Add test cases to test this using example private companies - chatGpt, Eridu, Anthropic.
6. Allow users to edit both tables to add more information or update these rows.
7. Every table should have createDateTime and lastUpdatedDateTime fields.
8. Create an investor table that will have following fields - investor name, description, investor type, total companies invested, total $ amount invested so far, location. Use specific queries to gather all this information via web search when adding a new investor into this table. 
