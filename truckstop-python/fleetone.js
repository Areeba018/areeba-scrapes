/*
https://apps.fleetone.com (Wex)

MC # 1288880
SALS GLOBAL TRANSPORT LLC

MC # 1560727
Inter Prime Cargo INC

MC # 001679
JRC TRANSPORTATION SERVICES LLC

MC # 186013
SUREWAY TRANSPORTATION
*/

const puppeteer = require("puppeteer");
const { PrismaClient } = require('@prisma/client')
const prisma = new PrismaClient()

const provider = "Fleet"
const cheerio = require('cheerio')

class Fleet {

    constructor(username, password) {
        this.username = username;
        this.password = password;
    }

    async init() {

        let config = {
            headless: "new",
            slowmo: 50,
            devtools: true,
            args: [
                '--start-maximized',
                '--no-sandbox'
            ]
        };

        if (this.browser) await this.browser.close()

        this.browser = await puppeteer.launch(config)
        this.page = (await this.browser.pages())[0]

        await this.page.goto(`https://apps.fleetone.com/FleetDocs/User/Login`).catch(e => {});

        // await this.page.type('#UserName', "Muzafar.1995@hotmail.com")
        // await this.page.type('#Password', "Factoring12345")

        await this.page.type('#UserName', this.username)
        await this.page.type('#Password', this.password)

        // debugger
        this.page.click('.fleet-primary')
        await this.page.waitForNavigation()

        console.log("Fleet Logged In")
    }

    close() {
        this.browser.close().catch(e => { });
    }

    async doLookup(mcNumbers, retries = 3) {
        const results = [];

        for (const mcNumber of mcNumbers) {

            await this.page.type('#mcSearch', mcNumber);
            this.page.click('#btnSearch');

            const response = await this.page.waitForResponse('https://apps.fleetone.com/FleetDocs/CreditLookup/get_credit_lookup_paginate');
            const responseBody = await response.json();

            let status = null;

            // Extract the value of the 'title' attribute from the first column of the first row
            const containsApprove = responseBody.table_data.includes('Approve');

            const containsDecline = responseBody.table_data.includes('Decline');

            const containsReview = responseBody.table_data.includes('Review');


            if(containsApprove){
                status = 1;
            }else if(containsReview){
                status = 2
            }else{
                status = 0;
            }

            console.log('Fleet Search Response:', status);

            await this.page.evaluate(() => window.stop())

            let data = {
                provider,
                mcNumber,
                isSupported: status,
                date: new Date()
            }

            results.push(data);

        }

        return results;

    }
}

module.exports = Fleet;
