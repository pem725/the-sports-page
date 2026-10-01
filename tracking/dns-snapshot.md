# DNS zone snapshot — thesportspage.net

Captured 2026-10-01 from the Porkbun API, full length.
**This is the rollback reference for the Cloudflare migration.** Every record
below must exist afterward, or something breaks — and the mail ones break
silently. Regenerate with:

```bash
python3 scripts/porkbun.py --snapshot thesportspage.net
```

13 records.

## ALIAS

```
thesportspage.net
    pem725.github.io
```

## CNAME

```
www.thesportspage.net
    pem725.github.io
```

## MX

```
thesportspage.net  prio=10
    fwd1.porkbun.com
thesportspage.net  prio=20
    fwd2.porkbun.com
```

## NS

```
thesportspage.net
    curitiba.porkbun.com
thesportspage.net
    fortaleza.porkbun.com
thesportspage.net
    maceio.porkbun.com
thesportspage.net
    salvador.porkbun.com
```

## TXT

```
_acme-challenge.thesportspage.net
    -KnC-6KfdlgXCjLHXX90UJA5PQgLqiMCBgMMkOX-8Jg
_acme-challenge.thesportspage.net
    obAGOBY4JYqy5J2_P4ii9NOELA8waG9S3RZVbn0-3wk
_dmarc.thesportspage.net
    v=DMARC1; p=quarantine; rua=mailto:25f8c5e6@mxtoolbox.dmarc-report.com; ruf=mailto:25f8c5e6@forensics.dmarc-report.com; fo=1
default._domainkey.thesportspage.net
    v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCf674xldUZIbyEQAsiSJWA9N5rgz14Ob1wTJX/tgmg9yPgrkAtZqWgC+y4KABmCp0+Hy5CTPHlvc6N4Ka+yCbwrYM1mtp72XhLGkRaQ2ZnUl8LKta1YHp3WBuCl1WTMqugpvd9h3/1/kNoknQuRI4jh79wFfZ2UT/3GlSe54QfXQIDAQAB
thesportspage.net
    v=spf1 include:_spf.porkbun.com ~all
```
