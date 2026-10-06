"""Write the synthetic multilingual sample corpus. Safe to re-run."""

from pathlib import Path

OUT = Path(__file__).resolve().parent / "samples"

BANNER = (
    "SAMPLE / SYNTHETIC — not affiliated with any bank. "
    "Northwind Community Bank is fictional. These pages are not a real product, "
    "not financial advice, and not customer data."
)

META = {
    "en": {
        "retail-loan": "Synthetic retail loan terms",
        "card-fees": "Synthetic debit card fees",
        "kyc": "Synthetic KYC checklist",
        "deposits": "Synthetic deposit terms",
        "fx-transfers": "Synthetic SWIFT transfer terms",
    },
    "ru": {
        "retail-loan": "Синтетические условия потребительского кредита",
        "card-fees": "Синтетические комиссии дебетовых карт",
        "kyc": "Синтетический чеклист KYC",
        "deposits": "Синтетические условия вкладов",
        "fx-transfers": "Синтетические условия переводов SWIFT",
    },
    "uz": {
        "retail-loan": "Iste'mol krediti bo'yicha sun'iy shartlar",
        "card-fees": "Debet karta komissiyalari bo'yicha sun'iy jadval",
        "kyc": "KYC bo'yicha sun'iy tekshiruv ro'yxati",
        "deposits": "Omonatlar bo'yicha sun'iy shartlar",
        "fx-transfers": "SWIFT o'tkazmalari bo'yicha sun'iy shartlar",
    },
}

PAGES = {
    "en": {
        "retail-loan": [
            "Northwind Community Bank, a fictional sample institution, offers a consumer cash loan. The minimum amount is 5 000 000 UZS. The maximum amount is 150 000 000 UZS. The tenor runs from 6 months to 60 months. The nominal annual interest rate is 24.9% for salaried clients and 27.5% for self-employed clients. The rate is fixed for the full tenor.",
            "Early repayment has no fee after the first 6 months. During the first 6 months the early repayment fee is 1.0% of the remaining principal. A loan up to 30 000 000 UZS is unsecured. A loan above 30 000 000 UZS requires one guarantor who is a resident individual. The late fee is 0.1% of the overdue amount per day and is capped at 15% of the overdue amount.",
            "A pre-approved salaried client receives a decision within 1 business day. Every other application receives a decision within 3 business days. The sample loan has no payment holiday. Credit insurance is optional and is not bundled into the loan.",
        ],
        "card-fees": [
            "The Classic debit card has an issuance fee of 50 000 UZS and an annual fee of 0 UZS. The Gold debit card has an issuance fee of 150 000 UZS and an annual fee of 120 000 UZS. Replacing a lost card costs the same as issuance for that card tier.",
            "ATM withdrawals on the Northwind network are free. Another domestic ATM charges 1% with a minimum of 3 000 UZS. An international ATM charges 2% with a minimum of 20 000 UZS. A card purchase in a foreign currency includes an FX markup of 1.5%. A branch cash advance costs 1% with a minimum of 10 000 UZS.",
            "A single contactless purchase at or below 100 000 UZS does not require a PIN. A purchase above 100 000 UZS requires a PIN. This sample schedule does not include a credit card. Cashback is not part of this sample schedule.",
        ],
        "kyc": [
            "A resident individual must present a passport or national ID card, a mobile phone number, a residential address, and a PINFL of 14 digits. A non-resident must present a passport and a visa or residence permit, plus an address abroad. A sole proprietor must present the registration certificate, a signed application, and a PINFL.",
            "A source-of-funds declaration is required when a single cash deposit or a single transfer is above 100 000 000 UZS. A politically exposed person receives enhanced due diligence. The fictional bank refuses the file when the identity document is expired or the photo does not match the applicant.",
            "Customer documents are refreshed every 36 months, or sooner when the passport expires. A minor account requires a parent or legal guardian and a birth certificate. The sample bank does not issue a debit card to a customer under 14 years of age.",
        ],
        "deposits": [
            "Maple Savings is a term deposit in this sample. The nominal annual rate is 18%. The term is 12 months. The minimum opening amount is 1 000 000 UZS. Interest is paid monthly. If the client withdraws before maturity, accrued interest for the current month is forfeited. Interest already paid for prior months is not clawed back.",
            "River Call is a call deposit in this sample. The nominal annual rate is 12%. There is no fixed term. The minimum balance is 500 000 UZS. Partial withdrawals are allowed. A withdrawal above 10 000 000 UZS needs 7 days of notice.",
            "The fictional deposit protection note in this sample covers up to 200 000 000 UZS per depositor at Northwind Community Bank. It is not a government scheme and it is not a real deposit-insurance product.",
        ],
        "fx-transfers": [
            "An outbound personal SWIFT transfer costs 0.3% of the amount, with a minimum of 50 000 UZS and a maximum of 500 000 UZS, plus any correspondent-bank fee. An inbound SWIFT transfer has no Northwind fee. A correspondent bank may still deduct its own fee. Supported currencies are USD, EUR, GBP, and RUB.",
            "Every outbound transfer requires a purpose code. The daily outbound limit without extra review is 10 000 USD equivalent. An amount above 10 000 USD equivalent goes through a compliance review that takes 2 business days.",
            "The same-day processing cut-off is 16:00 Asia/Tashkent (UTC+5). This sample service does not send crypto-asset transfers, anonymous third-party transfers, or transfers that omit the purpose code.",
        ],
    },
    "ru": {
        "retail-loan": [
            "Вымышленный Northwind Community Bank в этом образце предлагает потребительский кредит наличными. Минимальная сумма 5 000 000 UZS. Максимальная сумма 150 000 000 UZS. Срок от 6 месяцев до 60 месяцев. Номинальная годовая ставка 24.9% для зарплатных клиентов и 27.5% для самозанятых. Ставка фиксируется на весь срок.",
            "Досрочное погашение после первых 6 месяцев комиссии не имеет. В первые 6 месяцев комиссия за досрочное погашение составляет 1.0% от остатка основного долга. Кредит до 30 000 000 UZS выдается без обеспечения. Кредит выше 30 000 000 UZS требует одного поручителя, резидента. Пеня составляет 0.1% от просроченной суммы в день и ограничена 15% просроченной суммы.",
            "Предодобренный зарплатный клиент получает решение за 1 рабочий день. Любая другая заявка получает решение за 3 рабочих дня. В образце нет платежных каникул. Страхование кредита добровольное и не включается в кредит автоматически.",
        ],
        "card-fees": [
            "Дебетовая карта Classic: выпуск 50 000 UZS, годовая плата 0 UZS. Дебетовая карта Gold: выпуск 150 000 UZS, годовая плата 120 000 UZS. Замена утерянной карты стоит столько же, сколько выпуск карты того же уровня.",
            "Снятие в банкоматах сети Northwind бесплатно. Чужой банкомат внутри страны: 1% минимум 3 000 UZS. Международный банкомат: 2% минимум 20 000 UZS. Покупка по карте в иностранной валюте включает валютную надбавку 1.5%. Выдача наличных в отделении: 1% минимум 10 000 UZS.",
            "Одна бесконтактная покупка на сумму до 100 000 UZS включительно проходит без PIN. Покупка выше 100 000 UZS требует PIN. В этом образце нет кредитной карты. Кешбэк в этот образец не входит.",
        ],
        "kyc": [
            "Резидент предъявляет паспорт или ID-карту, номер мобильного телефона, адрес проживания и PINFL из 14 цифр. Нерезидент предъявляет паспорт и визу или вид на жительство, а также адрес за рубежом. Индивидуальный предприниматель предъявляет свидетельство о регистрации, подписанное заявление и PINFL.",
            "Декларация об источнике средств нужна, если один наличный взнос или один перевод выше 100 000 000 UZS. Публичное должностное лицо проходит усиленную проверку. Образец банка отклоняет досье, если документ просрочен или фотография не совпадает с заявителем.",
            "Документы клиента обновляются каждые 36 месяцев либо раньше, если паспорт истекает. Счет несовершеннолетнего открывается с родителем или опекуном и свидетельством о рождении. Образец банка не выпускает дебетовую карту клиенту младше 14 лет.",
        ],
        "deposits": [
            "Maple Savings в этом образце — срочный вклад. Номинальная годовая ставка 18%. Срок 12 месяцев. Минимальная сумма открытия 1 000 000 UZS. Проценты выплачиваются ежемесячно. При изъятии до конца срока проценты за текущий месяц сгорают. Уже выплаченные проценты за прошлые месяцы не взыскиваются обратно.",
            "River Call в этом образце — вклад до востребования. Номинальная годовая ставка 12%. Срок не фиксирован. Минимальный остаток 500 000 UZS. Частичное снятие разрешено. Снятие больше 10 000 000 UZS требует уведомления за 7 дней.",
            "Вымышленная оговорка о защите вклада в этом образце покрывает до 200 000 000 UZS на одного вкладчика в Northwind Community Bank. Это не государственная система и не реальный страховой продукт.",
        ],
        "fx-transfers": [
            "Исходящий личный перевод SWIFT стоит 0.3% от суммы, минимум 50 000 UZS и максимум 500 000 UZS, плюс комиссия банка-корреспондента. Входящий перевод SWIFT не имеет комиссии Northwind. Банк-корреспондент может удержать свою комиссию. Поддерживаемые валюты: USD, EUR, GBP и RUB.",
            "Каждый исходящий перевод требует код назначения платежа. Дневной исходящий лимит без дополнительной проверки — эквивалент 10 000 USD. Сумма выше эквивалента 10 000 USD проходит комплаенс-проверку за 2 рабочих дня.",
            "Отсечка для обработки в тот же день — 16:00 Asia/Tashkent (UTC+5). Этот образец не отправляет переводы криптоактивов, анонимные переводы третьим лицам и переводы без кода назначения.",
        ],
    },
    "uz": {
        "retail-loan": [
            "Hayoliy Northwind Community Bank ushbu namunada iste'mol naqd krediti taklif etadi. Minimal summa 5 000 000 UZS. Maksimal summa 150 000 000 UZS. Muddat 6 oydan 60 oygacha. Nominal yillik stavka maoshli mijozlar uchun 24.9% va o'zini o'zi band qilgan mijozlar uchun 27.5%. Stavka butun muddatga qat'iy belgilangan.",
            "Birinchi 6 oydan keyin muddatidan oldin qaytarish komissiyasiz. Birinchi 6 oy ichida muddatidan oldin qaytarish komissiyasi qolgan asosiy qarzning 1.0%. 30 000 000 UZS gacha kredit ta'minotsiz. 30 000 000 UZS dan yuqori kredit rezident bo'lgan bitta kafolatni talab qiladi. Kechiktirilgan to'lov peniyasi kuniga muddati o'tgan summaning 0.1% va muddati o'tgan summaning 15% dan oshmaydi.",
            "Oldindan ma'qullangan maoshli mijoz qarorni 1 ish kuni ichida oladi. Qolgan arizalar qarorni 3 ish kuni ichida oladi. Namunada to'lov ta'tili yo'q. Kredit sug'urtasi ixtiyoriy va kreditga majburan qo'shilmaydi.",
        ],
        "card-fees": [
            "Classic debet karta: chiqarish 50 000 UZS, yillik to'lov 0 UZS. Gold debet karta: chiqarish 150 000 UZS, yillik to'lov 120 000 UZS. Yo'qolgan kartani almashtirish shu darajadagi kartani chiqarish bilan bir xil turadi.",
            "Northwind tarmog'idagi bankomatdan yechish bepul. Boshqa ichki bankomat: 1% kamida 3 000 UZS. Xalqaro bankomat: 2% kamida 20 000 UZS. Chet el valyutasidagi karta xaridi 1.5% valyuta ustamasini o'z ichiga oladi. Filialda naqd pul olish: 1% kamida 10 000 UZS.",
            "100 000 UZS gacha bo'lgan bitta kontaktsiz xarid PIN talab qilmaydi. 100 000 UZS dan yuqori xarid PIN talab qiladi. Ushbu namunada kredit karta yo'q. Keshbek ushbu namunaga kirmaydi.",
        ],
        "kyc": [
            "Rezident pasport yoki ID-karta, mobil telefon raqami, yashash manzili va 14 raqamli PINFL taqdim etadi. Norezident pasport va viza yoki yashash guvohnomasi, shuningdek chet eldagi manzilni taqdim etadi. Yakka tartibdagi tadbirkor ro'yxatdan o'tish guvohnomasi, imzolangan ariza va PINFL taqdim etadi.",
            "Manba-mablag' deklaratsiyasi bitta naqd tushum yoki bitta o'tkazma 100 000 000 UZS dan yuqori bo'lsa talab qilinadi. Siyosiy ta'sirli shaxs kuchaytirilgan tekshiruvdan o'tadi. Namunaviy bank hujjat muddati o'tgan bo'lsa yoki surat arizachiga mos kelmasa ishni rad etadi.",
            "Mijoz hujjatlari har 36 oyda yoki pasport muddati tugasa undan oldin yangilanadi. Voyaga yetmagan hisob ota-ona yoki vasiy va tug'ilganlik haqida guvohnoma bilan ochiladi. Namunaviy bank 14 yoshgacha mijozga debet karta chiqarmaydi.",
        ],
        "deposits": [
            "Maple Savings ushbu namunada muddatli omonat. Nominal yillik stavka 18%. Muddat 12 oy. Ochish uchun minimal summa 1 000 000 UZS. Foiz har oy to'lanadi. Mijoz muddatidan oldin yechsa, joriy oy uchun hisoblangan foiz kuyadi. Oldingi oylar uchun to'langan foiz qaytarib olinmaydi.",
            "River Call ushbu namunada chaqirib olinadigan omonat. Nominal yillik stavka 12%. Qat'iy muddat yo'q. Minimal qoldiq 500 000 UZS. Qisman yechish mumkin. 10 000 000 UZS dan yuqori yechish uchun 7 kun oldin xabar beriladi.",
            "Ushbu namunadagi hayoliy omonat himoyasi eslatmasi Northwind Community Bankda bitta omonatchi uchun 200 000 000 UZS gacha qoplaydi. Bu davlat tizimi emas va haqiqiy sug'urta mahsuloti emas.",
        ],
        "fx-transfers": [
            "Chiquvchi shaxsiy SWIFT o'tkazmasi summaning 0.3% i, kamida 50 000 UZS va ko'pi bilan 500 000 UZS, ustiga korrespondent bank komissiyasi. Kiruvchi SWIFT o'tkazmasida Northwind komissiyasi yo'q. Korrespondent bank o'z komissiyasini ushlab qolishi mumkin. Qo'llab-quvvatlanadigan valyutalar: USD, EUR, GBP va RUB.",
            "Har bir chiquvchi o'tkazma to'lov maqsadi kodini talab qiladi. Qo'shimcha tekshiruvsiz kunlik chiquvchi limit 10 000 USD ekvivalenti. 10 000 USD ekvivalentidan yuqori summa 2 ish kunida komplayens tekshiruvidan o'tadi.",
            "Shu kunning o'zi qayta ishlash chegarasi 16:00 Asia/Tashkent (UTC+5). Ushbu namuna kriptoaktiv o'tkazmalarini, anonim uchinchi shaxs o'tkazmalarini va maqsad kodi yo'q o'tkazmalarni yubormaydi.",
        ],
    },
}


def render(language: str, topic: str) -> str:
    title = META[language][topic]
    doc_id = f"{topic}-{language}"
    pages = "\n\n".join(
        f"## Page {index}\n{text}" for index, text in enumerate(PAGES[language][topic], start=1)
    )
    return (
        f"---\n"
        f"doc_id: {doc_id}\n"
        f"topic: {topic}\n"
        f"language: {language}\n"
        f"title: {title}\n"
        f"---\n"
        f"{BANNER}\n\n"
        f"# {title}\n\n"
        f"{pages}\n"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for language, topics in PAGES.items():
        for topic in topics:
            path = OUT / f"{topic}-{language}.md"
            path.write_text(render(language, topic), encoding="utf-8")
            print(path.name)


if __name__ == "__main__":
    main()
