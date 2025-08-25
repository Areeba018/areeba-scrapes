/*
https://portal.otrsolutions.com (OTR Factoring)

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
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

const provider = "otr";
const cheerio = require('cheerio');

class Otr {

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

        if (this.browser) await this.browser.close();

        this.browser = await puppeteer.launch(config);
        this.page = (await this.browser.pages())[0];

        await this.page.goto(`https://portal.otrsolutions.com`).catch(e => {});

        await this.page.type('[type="email"]', this.username);
        await this.page.type('[type="password"]', this.password);

        // debugger
        this.page.click('.dx-button-text');
        await this.page.waitForNavigation();
        // debugger

        console.log('otr logged in');

        await this.page.evaluate(() => window.stop())
    }

    close() {
        this.browser.close().catch(e => { });
    }

    async doLookup(mcNumbers, retries = 3) {
        const results = [];

        for (const mcNumber of mcNumbers) {
            let ok = true;
            let json = await this.page.evaluate((mcNumber) => {
                return fetch(`https://portal.otrsolutions.com/Broker/GetCustomerListAsync?skip=0&take=15&sort=%5B%7B%22selector%22%3A%22Name%22%2C%22desc%22%3Afalse%7D%5D&filter=%5B%5B%22Name%22%2C%22contains%22%2C%221560727%22%5D%2C%22or%22%2C%5B%22McNumber%22%2C%22contains%22%2C%221560727%22%5D%5D&searchValue=${mcNumber}`, {
                    "headers": {
                        "accept": "application/json, text/javascript, */*; q=0.01",
                        "accept-language": "en-US;q=0.9,en;q=0.8",
                        "sec-ch-ua": "\"Chromium\";v=\"118\", \"Google Chrome\";v=\"118\", \"Not=A?Brand\";v=\"99\"",
                        "sec-ch-ua-mobile": "?0",
                        "sec-ch-ua-platform": "\"Windows\"",
                        "sec-fetch-dest": "empty",
                        "sec-fetch-mode": "cors",
                        "sec-fetch-site": "same-origin",
                        "x-requested-with": "XMLHttpRequest"
                    },
                    "referrer": "https://portal.otrsolutions.com/Broker",
                    "referrerPolicy": "origin-when-cross-origin",
                    "body": null,
                    "method": "GET",
                    "mode": "cors",
                    "credentials": "include"
                }).then(r => r.json()).catch(e => {
                    return { ok: false }
                })
            }, mcNumber);

            if (json.ok === false) {
                await this.init();
                return await this.doLookup(mcNumber, retries - 1)
            }

            let record = json.data.find(x => x.McNumber === mcNumber);
            let approved = false;

            if (record) {
                let json2 = await this.page.evaluate(pKey => {
                    return  fetch("https://portal.otrsolutions.com/Broker/CreditCheckAsync", {
                        "headers": {
                            "accept": "*/*",
                            "accept-language": "en-PH,en-US;q=0.9,en;q=0.8",
                            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                            "sec-ch-ua": "\"Chromium\";v=\"118\", \"Google Chrome\";v=\"118\", \"Not=A?Brand\";v=\"99\"",
                            "sec-ch-ua-mobile": "?0",
                            "sec-ch-ua-platform": "\"Windows\"",
                            "sec-fetch-dest": "empty",
                            "sec-fetch-mode": "cors",
                            "sec-fetch-site": "same-origin",
                            "x-requested-with": "XMLHttpRequest"
                        },
                        "referrer": "https://portal.otrsolutions.com/Broker",
                        "referrerPolicy": "origin-when-cross-origin",
                        "body": `customerPKey=${pKey}`,
                        "method": "POST",
                        "mode": "cors",
                        "credentials": "include"
                    }).then(r => r.json()).catch(e => {
                        return { ok: false }
                    })
                }, record.PKey);
                approved = !json2.data.text.includes("Not");
            }

            console.log('OTR Search Response:', approved);

            let data = {
                provider,
                mcNumber,
                isSupported: approved ? 1 : 0,
                date: new Date()
            };

            results.push(data);
        }

        return results;
    }
}

module.exports = Otr;
