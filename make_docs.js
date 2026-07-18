const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageNumber, Footer, Header
} = require('docx');
const fs = require('fs');

const RTL = { bidirectional: true };
const FONT = "Arial";

function rtlPara(text, opts = {}) {
  return new Paragraph({
    bidirectional: true,
    alignment: AlignmentType.RIGHT,
    ...opts,
    children: [new TextRun({ text, font: FONT, ...opts.run })],
  });
}

function heading1(text) {
  return new Paragraph({
    bidirectional: true,
    alignment: AlignmentType.RIGHT,
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, font: FONT, bold: true, size: 28, color: "1a4a2e" })],
    spacing: { before: 240, after: 120 },
  });
}

function heading2(text) {
  return new Paragraph({
    bidirectional: true,
    alignment: AlignmentType.RIGHT,
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, font: FONT, bold: true, size: 24 })],
    spacing: { before: 180, after: 80 },
  });
}

function bullet(text) {
  return new Paragraph({
    bidirectional: true,
    alignment: AlignmentType.RIGHT,
    numbering: { reference: "bullets", level: 0 },
    children: [new TextRun({ text, font: FONT, size: 22 })],
  });
}

function space() {
  return new Paragraph({ children: [new TextRun("")] });
}

// ── DOCUMENT 1: EULA ──────────────────────────────────────────────────────────
function makeEULA() {
  const children = [
    new Paragraph({
      bidirectional: true,
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "הסכם רישיון משתמש קצה (EULA)", font: FONT, bold: true, size: 36, color: "1a4a2e" })],
      spacing: { after: 80 },
    }),
    new Paragraph({
      bidirectional: true,
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "תוכנת Bridge Teacher", font: FONT, bold: true, size: 26, color: "555555" })],
      spacing: { after: 300 },
    }),

    rtlPara("קרא הסכם זה בעיון לפני השימוש בתוכנה. שימוש בתוכנה מהווה הסכמה לתנאים המפורטים להלן.", { run: { italics: true, size: 22, color: "555555" } }),
    space(),

    heading1("1. הגדרות"),
    rtlPara('בהסכם זה:', { run: { size: 22 } }),
    bullet('"התוכנה" — מוצר Bridge Teacher, לרבות כל עדכון או גרסה עתידית שלו.'),
    bullet('"המפתח" — יצחק תילוביץ, בעל זכויות היוצרים הבלעדיות בתוכנה.'),
    bullet('"המשתמש" — האדם או הגוף שרכש רישיון לשימוש בתוכנה.'),
    space(),

    heading1("2. מתן רישיון"),
    rtlPara("המפתח מעניק למשתמש רישיון אישי, מוגבל, בלתי-עביר ולא-בלעדי להתקין ולהשתמש בתוכנה על מחשב אחד בבעלות המשתמש.", { run: { size: 22 } }),
    rtlPara("הרישיון ניתן למשתמש יחיד בלבד ואינו ניתן להעברה לאחרים ללא אישור מפורש בכתב מהמפתח.", { run: { size: 22 } }),
    space(),

    heading1("3. הגבלות שימוש"),
    rtlPara("המשתמש אינו רשאי:", { run: { size: 22, bold: true } }),
    bullet("להעתיק, לשכפל או להפיץ את התוכנה בכל צורה שהיא."),
    bullet("למכור, להשכיר, להשאיל או להעביר את הרישיון לצד שלישי."),
    bullet("לבצע הנדסה לאחור (Reverse Engineering), פירוק (Decompile) או פיצוח של הקוד."),
    bullet("לשנות, לתרגם או ליצור עבודות נגזרות מהתוכנה."),
    bullet("להסיר או לשנות הודעות זכויות יוצרים המופיעות בתוכנה."),
    space(),

    heading1("4. זכויות יוצרים וקניין רוחני"),
    rtlPara("התוכנה, לרבות כל הקוד, העיצוב, הלוגיקה וחומרי העזר, הינה רכושו הבלעדי של יצחק תילוביץ. כל הזכויות שמורות.", { run: { size: 22 } }),
    rtlPara("הסכם זה אינו מעביר למשתמש כל זכות קניין רוחני בתוכנה.", { run: { size: 22 } }),
    space(),

    heading1("5. הגבלת אחריות"),
    rtlPara('התוכנה מסופקת "AS IS" — כפי שהיא — ללא כל אחריות מפורשת או משתמעת.', { run: { size: 22 } }),
    rtlPara("המפתח אינו אחראי לכל נזק ישיר, עקיף, מקרי או תוצאתי הנובע משימוש בתוכנה או מאי-יכולת לעשות בה שימוש.", { run: { size: 22 } }),
    space(),

    heading1("6. סיום ההסכם"),
    rtlPara("הסכם זה בתוקף עד לביטולו. הפרת תנאי כלשהו מהסכם זה תגרור את ביטול הרישיון אוטומטית וללא הודעה מוקדמת.", { run: { size: 22 } }),
    rtlPara("עם סיום ההסכם, המשתמש מחויב להסיר את התוכנה ממחשבו ולהשמיד את כל עותקיה ברשותו.", { run: { size: 22 } }),
    space(),

    heading1("7. חוק שחל"),
    rtlPara("הסכם זה כפוף לחוקי מדינת ישראל. כל סכסוך שיתעורר בקשר להסכם זה יידון בבתי המשפט המוסמכים בישראל.", { run: { size: 22 } }),
    space(),

    heading1("8. אישור וחתימה"),
    rtlPara("בחתימתי על הסכם זה אני מאשר כי קראתי, הבנתי והסכמתי לכל תנאיו.", { run: { size: 22 } }),
    space(), space(),

    // Signature table
    new Table({
      width: { size: 9026, type: WidthType.DXA },
      columnWidths: [4513, 4513],
      rows: [
        new TableRow({ children: [
          new TableCell({
            width: { size: 4513, type: WidthType.DXA },
            borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
            children: [new Paragraph({ bidirectional: true, alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "חתימה: _______________________", font: FONT, size: 22 })] })],
          }),
          new TableCell({
            width: { size: 4513, type: WidthType.DXA },
            borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
            children: [new Paragraph({ bidirectional: true, alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "תאריך: _______________________", font: FONT, size: 22 })] })],
          }),
        ]}),
        new TableRow({ children: [
          new TableCell({
            width: { size: 4513, type: WidthType.DXA },
            borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
            children: [new Paragraph({ bidirectional: true, alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "שם מלא: _______________________", font: FONT, size: 22 })] })],
          }),
          new TableCell({
            width: { size: 4513, type: WidthType.DXA },
            borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
            children: [new Paragraph({ children: [] })],
          }),
        ]}),
      ],
    }),
  ];

  return new Document({
    styles: {
      default: { document: { run: { font: FONT, size: 22 } } },
    },
    numbering: {
      config: [{
        reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.RIGHT,
          style: { paragraph: { indent: { right: 720, hanging: 360 }, bidirectional: true } } }],
      }],
    },
    sections: [{
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
        bidi: true,
      },
      footers: {
        default: new Footer({ children: [new Paragraph({
          bidirectional: true,
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Bridge Teacher © יצחק תילוביץ — עמוד ", font: FONT, size: 18, color: "888888" }),
            new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "888888" }),
          ],
        })] }),
      },
      children,
    }],
  });
}

// ── DOCUMENT 2: User Manual ───────────────────────────────────────────────────
function makeManual() {
  const children = [
    new Paragraph({
      bidirectional: true,
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Bridge Teacher — מדריך למשתמש", font: FONT, bold: true, size: 40, color: "1a4a2e" })],
      spacing: { after: 80 },
    }),
    new Paragraph({
      bidirectional: true,
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "עזרה למורה ברידג'", font: FONT, size: 28, color: "555555", italics: true })],
      spacing: { after: 320 },
    }),

    heading1("מה התוכנה עושה?"),
    rtlPara("Bridge Teacher היא תוכנת שולחן עבודה למורי ברידג'. התוכנה מאפשרת יצירת לוחות אימון מותאמים אישית לפי שיטת Acol — 5 קלפים במיגור, 1NT חזק 15-17.", { run: { size: 22 } }),
    rtlPara("המורה מגדיר אילוצים לכל שחקן (כוח, סוג יד, תמיכה וכו') והתוכנה מייצרת לוחות עם הכרזות אוטומטיות מלאות, מוכנים להדפסה.", { run: { size: 22 } }),
    space(),

    heading1("התקנה והפעלה"),
    bullet("לחץ פעמיים על BridgeTeacher.exe"),
    bullet("לא נדרשת התקנה — קובץ אחד, מריץ ישירות"),
    bullet("דרישות מערכת: Windows 10 / Windows 11"),
    bullet("גודל קובץ: כ-10 MB"),
    space(),

    heading1("הגדרות שיטה"),
    rtlPara("בחלק העליון של המסך ניתן לשנות את פרמטרי השיטה:", { run: { size: 22 } }),
    bullet("מיגור: 4 קלפים / 5 קלפים (ברירת מחדל: 5 קלפים)"),
    bullet("1NT: 12-14 / 15-17 (ברירת מחדל: 15-17)"),
    bullet("מינור: 2 קלפים / 3 קלפים (ברירת מחדל: 3 קלפים)"),
    space(),

    heading1("הגדרת שחקנים"),
    rtlPara("המסך מכיל 4 פאנלים — צפון, מזרח, דרום, מערב. כל שחקן יכול להיות באחד מהמצבים הבאים:", { run: { size: 22 } }),
    space(),
    heading2("חופשי"),
    rtlPara("ללא אילוצים — התוכנה תחלק יד אקראית.", { run: { size: 22 } }),
    heading2("פותח"),
    rtlPara("הגדר:", { run: { size: 22 } }),
    bullet("כוח: חלש 12-14 / בינוני 15-17 / חזק 18-21"),
    bullet("סוג פתיחה: מיגור (♥/♠) / מינור (♣/♦) / 1NT"),
    heading2("משיב"),
    rtlPara("לאחר הגדרת פותח, השחקן השותף הופך למשיב אוטומטית. הגדר:", { run: { size: 22 } }),
    bullet("כוח משיב: חלש 6-9 / בינוני 10-12 / חזק 13+"),
    bullet("סוג תשובה: תמיכה / 1NT / 1♠ / סטיימן / טרנספר ♥/♠ / 2NT"),
    space(),

    heading1("יצירת לוחות"),
    bullet("בחר מספר לוחות (1 עד 36)"),
    bullet("בחר דילר (אופציונלי: צפון / מזרח / דרום / מערב / ללא)"),
    bullet('לחץ "⚡ צור לוחות"'),
    bullet("הלוחות נפתחים בחלון הדפסה נפרד"),
    space(),

    heading1("הדפסה"),
    bullet("4 לוחות לעמוד, פורמט A4 לאורך"),
    bullet("כל לוח כולל: פריסת 4 ידיים + מצפן + טבלת ניקוד ריקה"),
    bullet('לחץ "🖨 הדפס" לשליחה למדפסת'),
    space(),

    heading1("שיעורים מוכנים"),
    rtlPara('כפתור "📚 שיעורים" מציג קבוצות ידיים מוכנות מראש לפי נושא:', { run: { size: 22 } }),
    bullet("1NT — פס, סטיימן גיים/הזמנה, טרנספר ♥/♠, 3NT"),
    bullet("מיגורים — 1♥/1♠ עם כל סוגי התשובות"),
    bullet("מינורים — 1♣/1♦ עם כל סוגי התשובות"),
    bullet("סלאם — Gerber, RKCB, הזמנת סלאם"),
    bullet("פתיחות 2 חלשות — 2♥/2♠"),
    bullet("2♣ חזקה — תשובה שלילית/חיובית"),
    bullet("2NT (20-22) — סטיימן, טרנספר, 3NT"),
    space(),

    heading1("כפתורים נוספים"),
    bullet('"אפס" — מנקה את כל ההגדרות ומחזיר לברירת מחדל'),
    bullet('"📋 הכרזות ✓/✗" — הצג/הסתר הכרזות על הלוחות'),
    space(),

    heading1("יצירת קשר ותמיכה"),
    rtlPara("לשאלות, הצעות שיפור ותמיכה טכנית:", { run: { size: 22 } }),
    rtlPara("יצחק תילוביץ — מורה ברידג'", { run: { size: 22, bold: true } }),
    space(),

    new Paragraph({
      bidirectional: true,
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Bridge Teacher © יצחק תילוביץ — כל הזכויות שמורות", font: FONT, size: 18, color: "888888", italics: true })],
      spacing: { before: 400 },
    }),
  ];

  return new Document({
    styles: {
      default: { document: { run: { font: FONT, size: 22 } } },
    },
    numbering: {
      config: [{
        reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.RIGHT,
          style: { paragraph: { indent: { right: 720, hanging: 360 }, bidirectional: true } } }],
      }],
    },
    sections: [{
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
        bidi: true,
      },
      footers: {
        default: new Footer({ children: [new Paragraph({
          bidirectional: true,
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Bridge Teacher — מדריך למשתמש | עמוד ", font: FONT, size: 18, color: "888888" }),
            new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "888888" }),
          ],
        })] }),
      },
      children,
    }],
  });
}

// ── Write files ────────────────────────────────────────────────────────────────
async function main() {
  const eula = makeEULA();
  const manual = makeManual();

  const [b1, b2] = await Promise.all([Packer.toBuffer(eula), Packer.toBuffer(manual)]);
  fs.writeFileSync('D:\\bridge-teacher1\\הסכם_רישיון.docx', b1);
  fs.writeFileSync('D:\\bridge-teacher1\\מדריך_למשתמש.docx', b2);
  console.log('Done: הסכם_רישיון.docx + מדריך_למשתמש.docx');
}

main().catch(console.error);
