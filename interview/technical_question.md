שאלות זום
אופטימיזציה ל-DB - Partitioning vs Index
יש לנו DB בנפח של כמה טרה-בייטים. [הכנס סוג DB - למשל Postgres / BigQuery / Snowflake]. אנחנו חווים עומס בשאילתות של לקוחות שמריצים תהליכים כבדים, ואנחנו חייבים לייעל את זה. איך היית ניגש לבעיה? 
דוגמה קונקרטית
תחשוב על טבלת client_events של 5TB. לקוחות שולפים משם דאטה כדי לייצר דוחות יומיים, והם בדרך כלל מפלטרים לפי client_id ולפי event_date. השאילתות איטיות מאוד."

✅ מה לחפש (Green Flags):
תחקור תחילה: שואל על פיזור נתונים, סכמה, או סוגי שאילתות לפני שזורק פתרונות.
Archiving/Cleanup: מציע למחוק/לארכב Legacy Data לפני שמתחילים לאנדקס.
Indexes: מתאים לערכים ייחודיים (High Cardinality, e.g., client_id). מבין שזה מאט כתיבה (Writes).
Partitions: מתאים לטווחים (Range, e.g., event_date, region). מאפשר Partition Pruning.
Overhead: מבין שיותר מדי מחיצות (Small Files) דופק את הביצועים.
❌ נורות אדומות (Red Flags):
יורה פתרונות: לא שואל שאלות הבהרה קודם.
Over-Indexing: "נשים אינדקס על כל עמודה".
Bad Partitioning: מחיצה על עמודה עם המון ערכים שונים (למשל user_id).
"תמיד טוב": חושב שאינדקסים/מחיצות הם קסם נטול חסרונות.

שאלת חילוץ: "אם אני עושה פרטישן לפי תאריך מפורט (עד רמת השעה) בטבלה של 10 שנים - מה לדעתך תהיה הבעיה?" (תשובה מצופה: Overhead מטורף, יותר מדי פרטישנים).
איך אינדקס חדש ישפיע על תהליכי ה-Ingestion שלנו?


Data Enrichment & Product Thinking
יש לנו דאטה-סט של משתמשים שכולל שם מלא, חברה, וקצת פרטי קשר אישיים. להרבה מהם חסר האימייל של העבודה (Work Email). המטרה שלך היא להגדיל את ה-Coverage (כיסוי) של האימיילים העסקיים. איך תיגש לזה?
זו בעיה הסתברותית, לא דטרמיניסטית. אנחנו מחפשים יכולת הסקה מתוך הקיים (Pattern Recognition), הבנה של ולידציה, וזהירות מ-False Positives (העדפת איכות על פני כמות).

✅ מה לחפש (Green Flags / Hints):
Inference (הסקה): משתמש באימיילים קיימים מאותה חברה כדי להבין את התבנית (למשל first.last@ או f.last@).
Candidate Generation: מייצר כמה אפשרויות לאותו אדם, ולא מסתמך על ניחוש אחד.
Validation (קריטי): לא סומך על הניחוש! מוודא מול צד ג' (Verification API, SMTP check, Cross-reference עם דאטה מהווב).
Precision vs. Recall: מבין שעדיף דאטה חסר מאשר דאטה שגוי (אימיילים שגויים יוצרים Bounces ופוגעים במוניטין השליחה של החברה).
Edge Cases: מתייחס לשמות נפוצים (John Smith), שמות חיבה, או חברות עם כמה דומיינים.
Do No Harm: מוודא שלעולם לא דורסים אימייל קיים ומאומת.
❌ נורות אדומות (Red Flags):
הגישה הנאיבית: "פשוט ניקח שם פרטי נקודה שם משפחה ונוסיף את הדומיין של החברה." (מתייחס לזה כבעיה דטרמיניסטית).
אפס ולידציה: מניח שמה שייצרנו הוא נכון, בלי לבדוק או לבקש פידבק.
Blind Overwrite: אין מנגנון שמגן על דאטה קיים.
"תבנית אחת לכולם": מניח שלחברה יש רק פורמט אימייל אחד בלי לבדוק חריגים.
❓ שאלות חילוץ / הקשחה:
"נניח שניחשנו את האימייל j.smith@google.com. איך תדע אם זה באמת הוא בלי לשלוח לו מייל?" (מצופה שידבר על פנייה ל-API, בדיקת סטטוס בשרת הדואר, וכו').
"מה תעשה בחברה גדולה אם יש שני אנשים שקוראים להם 'David Cohen'?" * "אם האלגוריתם שלך מצא אימייל, אבל כבר יש לו בחשבון אימייל אחר. מה תעשה?"

פעולות דאטה יקרות (Spark / Distributed Data)
פייפליין ה-Spark שלנו נהיה מאוד איטי ויקר לאחרונה. כשנסתכל ב-UI, נראה שהבעיה היא בשלב ה-Shuffle. ממה בדרך כלל נוצר Shuffle? 

ואילו שיטות וכלים יש לך כדי לייעל פעולות יקרות כמו Joins או GroupBy?

✅ מה לחפש (Green Flags & Hints):
זיהוי Shuffle: מבין שזה קורה כשדאטה עובר בין Nodes, בעיקר בפעולות של Join, GroupBy, Distinct, ו-Window Functions.
סוגי Joins:
Broadcast Hash Join: חובה להזכיר! הדרך הכי טובה לג'וין של טבלה ענקית עם טבלה קטנה (Dimensions/Lookups) – חוסך Shuffle לחלוטין.
Sort-Merge Join: לחיבור שתי טבלאות ענקיות (מציע Bucketing כדי לייעל).
Repartition vs Coalesce:
Repartition = עושה Shuffle. טוב בשביל לחלק מחדש דאטה לא מאוזן (Data Skew).
Coalesce = לא עושה Shuffle! מקטין מספר מחיצות מקומיות בלבד (מעולה לפני כתיבה ל-Storage).
Data Skew: מבין ש-GroupBy על מפתח עם המון ערכים זהים יחנוק Executor אחד.
❌ נורות אדומות (Red Flags):
לא יודע מה זה Shuffle: חושב שג'וינים קורים בזיכרון של שרת אחד.
משתמש ב-Repartition להכל: מחלק דאטה מחדש בלי צורך במקום להשתמש ב-Coalesce, וגורם ל-Overhead מטורף.
ג'וין נאיבי: עושה Standard Join על טבלת מיליארד שורות מול טבלה של מאה שורות (במקום Broadcast).
❓ שאלות חילוץ:
"יש לי טבלה של 5 טרה-בייט (Transactions) שאני רוצה לג'וין לטבלה של 10 מגה-בייט (Countries). איך היית כותב את זה בספארק?" (תשובה מצופה: Broadcast).
"אחרי פילטר כבד, נשארתי עם 1000 מחיצות קטנות. אני רוצה להקטין ל-10 מחיצות כדי לכתוב ל-S3. תשתמש ב-Repartition או Coalesce? ולמה?"


שאלות פרונטליות
דיבוג תהליך שהפך לאיטי (Performance Drop / Data Skew)
תהליך מתוזמן (Scheduled Job) שלנו הפך פתאום לאיטי פי 2 החל מיום מסוים. איך היית עולה על זה? מאיפה היית מתחיל לחקור את הסיבה? ואיך היית מונע מקרים דומים בעתיד?"
רקע למראיין: מדובר בתהליך נתונים (כמו Spark). הסיבה לאיטיות יכולה להיות תשתיתית, אבל לרוב מדובר בשינוי בנתונים (נפח, כפילויות, סכמה או Data Skew).

✅ מה לחפש (Green Flags & Hints):
1. גילוי (Detection): Monitoring: התראות (Alerts) על חריגה בזמני ריצה מתמשכים (SLA breach).
2. חקירה (Investigation) - Data First:
נפח נתונים (Volume): הרצת Select count(*) לפי ימים כדי לראות אם כמות הדאטה קפצה
כפילויות (Duplicates): דאטה שאמור להיות ייחודי (Distinct) פתאום מגיע כפול (למשל linkedin_url או email). גורם להתנפחות ב-Joins.
בדיקת סכמה (Schema Changes): האם הסכמה השתנתה? שדות חדשים? טייפים שהשתנו?
Data Skew / Group By: האם הפיזור של המפתח שעליו עושים GroupBy השתנה פתאום והפך לכבד מאוד עבור מפתח ספציפי.
3. חקירה (Investigation) - תשתית:
כלים: הסתכלות ב-Spark UI כדי לזהות צווארי בקבוק (למשל Task שנתקע אחרי כולם).
קלאסטר: בעיות חומרה, זיכרון, או "שכנים רועשים" (Noisy neighbors) בקלאסטר.
4. מניעה (Prevention):
Data Quality Checks / Unit Tests: הוספת בדיקות כשגרה לפני שמכניסים נתונים (למשל ציפייה למספר שורות סביר).
אכיפת ייחודיות (Uniqueness): ולידציה ששדות מזהים הם אכן ייחודיים ולא מכילים כפילויות/Nulls.
Schema Validation: חסימה או התראה אם הסכמה לא תואמת למה שהפייפליין מצפה לקבל.
❌ נורות אדומות (Red Flags):
מתעלם מהדאטה: קופץ ישר להוסיף עוד שרתים/זיכרון לקלאסטר בלי לבדוק את הדאטה
חוסר בכלים: לא מזכיר הצצה ללוגים, Spark UI, או לוחות בקרה.
אין חשיבה קדימה: לא מציע דרכים למנוע את הבעיה בעתיד (Data Contracts / Validations).
❓ שאלות חילוץ:
"אם הסתכלת ב-Spark UI וראית ש-99% מהמשימות סיימו תוך דקה, ואחת רצה שעתיים - מה זה אומר לך על הדאטה?" (תשובה מצופה: Data Skew / מפתח GroupBy עמוס מדי).
"איך תדע ששדה אימייל שאמור להיות יוניקי, לא גרם להתנפחות של הנתונים ב-Join?"

שימוש ב-Cache מול שירות צד ג' יקר
יש לנו תהליך שמושך נתונים משירות צד ג' (למשל פוסטים של חברות מלינקדאין). הקריאות ל-API הזה מאוד יקרות לנו, גם בכסף וגם בזמן ריצה. איך ניתן לייעל?
אנחנו רוצים להוסיף שכבת Cache כדי לחסוך עלויות ועדיין לשרת את הלקוחות בצורה טובה. איך היית מתכנן את זה, ומה הסכנות?
💡 רקע למראיין: המטרה היא לבדוק הבנה של טרייד-אופים במערכות מבוזרות, לא רק להגיד "נשים Redis".

✅ מה לחפש (Green Flags & Hints):
TTL (Time To Live): חייב להזכיר את המושג. הגדרה מתי הדאטה פג תוקף (למשל, פוסט לינקדאין אפשר לשמור ל-24 שעות).
אסטרטגיות Invalidation: מתי מוחקים דאטה מהקאש באופן יזום.
Negative Caching / שגיאות: התייחסות למה קורה אם ה-API מחזיר שגיאה (לא רוצים לקאשש אותה!).
❌ נורות אדומות (Red Flags):
"נשמור לנצח": התעלמות מבעיית ה-Freshness (הדאטה מתיישן).
Caching Blindly: שומרים את התשובה כמו שהיא בלי לבדוק אותה. (מוביל לזה שנקאשש תשובה מושחתת/שגיאה 500 וניתקע איתה ב-Cache עד שה-TTL יפוג).
התעלמות מנפח: לא חושב על פינוי זיכרון ב-Cache כשהוא מתמלא (Eviction policies כמו LRU).
❓ שאלות חילוץ:
"מה קורה אם לינקדאין החזירו לנו בטעות שגיאה 500 או JSON שבור, ואנחנו שומרים את זה ב-Cache?"
"לקוח מתלונן שהוא ערך את הפוסט שלו לפני שעה, אבל אצלנו עדיין רואים את הישן. למה זה קורה ואיך נטפל?"
איך עובד lru?
ניהול שינויים בסכמה
יש לנו את הטבלה company_enriched

company_id, domain, company_name, country, linkedin_url, employee_count/range

 - אנחנו רוצים להחליף את העמודה employee_count  ל-employee_range. 
Before: Employee_Count: 150 
After: Employee_Range: “[100 - 200]”
יש צרכנים למטה שעדיין משתמשים בה. מה הדרך הנכונה לעשות את זה, וממה כדאי להימנע?"
💡 רקע למראיין: הנתונים שונים (מספר מול טווח), ויש צרכני BI ו-ML פעילים.

✅ מה לחפש (Green Flags):
Parallel run: הוספת החדש בלי למחוק את הישן.
Deprecation: סימון העמודה כישנה + הגדרת לו"ז להסרה.
תקשורת: מיפוי צרכנים והודעה מראש.
מוניטורינג: וידוא שאף אחד לא קורא את הישן לפני המחיקה.
בטיחות: תוכנית Rollback או Versioning לטבלה.
❌ נורות אדומות (Red Flags):
Hard cut: מחיקה והחלפה באותו רליס.
תקשורת בדיעבד: לעשות את השינוי ורק אז להודיע.
"סמוך": להניח שהצרכנים יסתדרו לבד או שלא משתמשים בעמודה.
קומבינות דאטה: לזייף מספר מדויק מהטווח רק כדי לשמור על שם העמודה.
בדיקה צרה: לוודא רק שהפייפליין עצמו רץ (התעלמות מצרכני הקצה).
❓ שאלות חילוץ:
"איך תדע מתי אפשר פיזית למחוק את העמודה?"
"מה יקרה למודל ה-ML עכשיו?"




Attachments:

Optimize - q1
client_events
--------------------------------------------------------------------------------------------------------
| client_id | event_date | event_time | event_type | device  | country | revenue | payload        |
--------------------------------------------------------------------------------------------------------
| 123       | 2002-01-01 | 08:12:33   | click      | mobile  | US      | 0.00    | {...}          |
| 456       | 2003-01-01 | 09:45:10   | view       | desktop | UK      | 0.00    | {...}          |
| 123       | 2007-01-01 | 10:01:55   | add_cart   | mobile  | US      | 0.00    | {...}          |
| 789       | 2024-01-01 | 11:22:11   | click      | tablet  | DE      | 0.00    | {...}          |
| 123       | 2024-01-02 | 07:55:02   | purchase   | mobile  | US      | 59.99   | {...}          |
| 222       | 2024-01-02 | 08:14:44   | view       | desktop | FR      | 0.00    | {...}          |
| 456       | 2024-01-03 | 12:33:21   | click      | mobile  | UK      | 0.00    | {...}          |
| 999       | 2024-01-03 | 13:02:09   | purchase   | desktop | CA      | 120.00  | {...}          |
| 123       | 2024-01-04 | 15:44:18   | click      | mobile  | US      | 0.00    | {...}          |
| 321       | 2025-01-05 | 16:20:30   | view       | tablet  | IN      | 0.00    | {...}          |
| 654       | 2025-01-05 | 17:11:42   | add_cart   | mobile  | BR      | 0.00    | {...}          |
| 123       | 2025-01-06 | 18:09:55   | click      | mobile  | US      | 0.00    | {...}          |
| 888       | 2026-01-06 | 19:25:37   | purchase   | desktop | AU      | 75.50   | {...}          |
| 777       | 2026-01-07 | 20:41:12   | click      | mobile  | US      | 0.00    | {...}          |
| ...                                                                                                  |
| ... billions of rows across years, thousands of clients, all mixed together ...                     |
--------------------------------------------------------------------------------------------------------
Total size: ~5TB


Senior Data Engineer Interview Design Task
Goal
Design a scalable pipeline that converts unstructured company news into structured business events.
Context 
You are building an "Event Generator" system. Every day, the platform receives large volumes of news articles about companies from multiple sources (news feeds, web scraping, and third-party providers).
The business goal is to transform raw article text into high-quality events that can be consumed by downstream products (search, alerts, CRM enrichment, and analytics).
Examples of event types:
Funding round announced
Executive change
Merger or acquisition
Product launch
Input: Raw article text/HTML about a company event. 
Target Output Example:
JSON
{
  "product_name": "iPhone 18 Pro",
  "product_description": "Apple's new flagship smartphone with improved camera and on-device AI features.",
  "event_timestamp_utc": "2026-09-10T17:00:00Z",
  "title": "Apple launches iPhone 18 Pro at annual keynote",
  "snippet": "Apple unveiled the iPhone 18 Pro, highlighting camera upgrades...",
  "link": "https://news.example.com/apple-iphone-18-pro-launch"
}
Task: Please walk me through the end-to-end architecture for this pipeline.
