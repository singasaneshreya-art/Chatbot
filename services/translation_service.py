import os
import re
import requests

# Local translations for welcome messages, standard responses, chips, and static notifications
LOCAL_TRANSLATIONS = {
    # Welcome messages
    "👋 Hi! I'm **Support AI** — your AI-powered customer service agent.\n\nI can help you track your **order**, process a **refund**, or check our **support hours**! What can I do for you today?": {
        'hi': "👋 नमस्ते! मैं **सपोर्ट एआई** हूँ — आपका एआई-संचालित ग्राहक सेवा एजेंट।\n\nमैं आपके **ऑर्डर** को ट्रैक करने, **रिफंड** संसाधित करने, या हमारे **सपोर्ट के घंटे** देखने में आपकी मदद कर सकता हूँ! आज मैं आपके लिए क्या कर सकता हूँ?",
        'es': "👋 ¡Hola! Soy **Support AI**, tu agente de servicio al cliente impulsado por IA.\n\n¡Puedo ayudarte a rastrear tu **pedido**, procesar un **reembolso** o verificar nuestro **horario de atención**! ¿Qué puedo hacer por ti hoy?",
        'fr': "👋 Salut! Je suis **Support AI** — votre agent de service client alimenté par l'IA.\n\nJe peux vous aider à suivre votre **commande**, traiter un **remboursement** ou vérifier nos **heures d'ouverture**! Que puis-je faire pour vous aujourd'hui?",
        'de': "👋 Hallo! Ich bin **Support AI** – Ihr KI-gestützter Kundendienstmitarbeiter.\n\nIch kann Ihnen helfen, Ihre **Bestellung** zu verfolgen, eine **Rückerstattung** zu bearbeiten oder unsere **Supportzeiten** zu überprüfen! Was kann ich heute für Sie tun?",
        'ja': "👋 こんにちは！私は**Support AI**です。AIを搭載したカスタマーサービスエージェントです。\n\n**注文**の追跡、**返金**の手続き、**サポート時間**の確認などをお手伝いできます！本日はどのようなご用件でしょうか？"
    },
    
    # Standard Chips
    "Track my order": {
        'hi': "मेरा ऑर्डर ट्रैक करें",
        'es': "Rastrear mi pedido",
        'fr': "Suivre ma commande",
        'de': "Meine Bestellung verfolgen",
        'ja': "注文を追跡する"
    },
    "I need a refund": {
        'hi': "मुझे रिफंड चाहिए",
        'es': "Necesito un reembolso",
        'fr': "J'ai besoin d'un remboursement",
        'de': "Ich brauche eine Rückerstattung",
        'ja': "返金が必要です"
    },
    "What are your hours?": {
        'hi': "आपके काम के घंटे क्या हैं?",
        'es': "¿Cuáles son sus horas de atención?",
        'fr': "Quelles sont vos heures d'ouverture?",
        'de': "Wie sind Ihre Öffnungszeiten?",
        'ja': "営業時間は何時ですか？"
    },
    "Get My Order ID": {
        'hi': "मेरा ऑर्डर आईडी प्राप्त करें",
        'es': "Obtener mi ID de pedido",
        'fr': "Obtenir mon ID de commande",
        'de': "Bestell-ID abrufen",
        'ja': "注文IDを取得する"
    },
    "Get order id": {
        'hi': "मेरा ऑर्डर आईडी प्राप्त करें",
        'es': "Obtener mi ID de pedido",
        'fr': "Obtenir mon ID de commande",
        'de': "Bestell-ID abrufen",
        'ja': "注文IDを取得する"
    },
    "Back to main menu": {
        'hi': "मुख्य मेनू पर वापस जाएं",
        'es': "Volver al menú principal",
        'fr': "Retour au menu principal",
        'de': "Zurück zum Hauptmenü",
        'ja': "メインメニューに戻る"
    },
    "Cancel": {
        'hi': "रद्द करें",
        'es': "Cancelar",
        'fr': "Annuler",
        'de': "Abbrechen",
        'ja': "キャンセル"
    },
    "Yes, issue refund": {
        'hi': "हाँ, रिफंड जारी करें",
        'es': "Sí, emitir reembolso",
        'fr': "Oui, émettre le remboursement",
        'de': "Ja, Rückerstattung ausstellen",
        'ja': "はい、返金を発行します"
    },
    "Contact to Customer": {
        'hi': "ग्राहक सहायता से संपर्क करें",
        'es': "Contactar al servicio al cliente",
        'fr': "Contacter le service client",
        'de': "Kundenservice kontaktieren",
        'ja': "カスタマーサポートに連絡する"
    },
    "Track GPS": {
        'hi': "जीपीएस ट्रैक करें",
        'es': "Rastrear GPS",
        'fr': "Suivre le GPS",
        'de': "GPS verfolgen",
        'ja': "GPSを追跡する"
    },
    "Refund Options": {
        'hi': "रिफंड के विकल्प",
        'es': "Opciones de reembolso",
        'fr': "Options de remboursement",
        'de': "Rückerstattungsoptionen",
        'ja': "返金オプション"
    },
    "Retry": {
        'hi': "पुनः प्रयास करें",
        'es': "Reintentar",
        'fr': "Réessayer",
        'de': "Wiederholen",
        'ja': "再試行"
    },
    "Simulate Claude Response": {
        'hi': "क्लाउड प्रतिक्रिया का अनुकरण करें",
        'es': "Simular respuesta de Claude",
        'fr': "Simuler la réponse de Claude",
        'de': "Claude-Antwort simulieren",
        'ja': "Claudeの応答をシミュレートする"
    },
    "Hello again": {
        'hi': "फिर से नमस्ते",
        'es': "Hola de nuevo",
        'fr': "Bonjour à nouveau",
        'de': "Hallo noch einmal",
        'ja': "こんにちは、また"
    },

    # Standard responses from app.py
    "👋 Hello! Welcome to NexSupport. I can help you track your **order**, process a **refund**, or check our **support hours**! What can I do for you today?": {
        'hi': "👋 नमस्ते! नेक्ससपोर्ट में आपका स्वागत है। मैं आपके **ऑर्डर** को ट्रैक करने, **रिफंड** संसाधित करने, या हमारे **सपोर्ट के घंटे** देखने में आपकी मदद कर सकता हूँ! आज मैं आपके लिए क्या कर सकता हूँ?",
        'es': "👋 ¡Hola! Bienvenido a NexSupport. ¡Puedo ayudarte a rastrear tu **pedido**, procesar un **reembolso** o verificar nuestro **horario de atención**! ¿Qué puedo hacer por ti hoy?",
        'fr': "👋 Bonjour! Bienvenue chez NexSupport. Je peux vous aider à suivre votre **commande**, traiter un **remboursement** ou vérifier nos **heures d'ouverture**! Que puis-je faire pour vous aujourd'hui?",
        'de': "👋 Hallo! Willkommen bei NexSupport. Ich kann Ihnen helfen, Ihre **Bestellung** zu verfolgen, eine **Rückerstattung** zu bearbeiten oder unsere **Supportzeiten** zu überprüfen! Was kann ich heute für Sie tun?",
        'ja': "👋 こんにちは！NexSupportへようこそ。**注文**の追跡、**返金**の手続き、**サポート時間**の確認などをお手伝いできます！本日はどのようなご用件でしょうか？"
    },
    "👋 Hi there! NexSupport is at your service. Let me know if you have questions about your recent **orders** or **refunds**!": {
        'hi': "👋 नमस्ते! नेक्ससपोर्ट आपकी सेवा में है। मुझे बताएं कि क्या आपके पास अपने हालिया **ऑर्डर** या **रिफंड** के बारे में प्रश्न हैं!",
        'es': "👋 ¡Hola! NexSupport está a tu servicio. ¡Déjame saber si tienes preguntas sobre tus **pedidos** recientes o **reembolsos**!",
        'fr': "👋 Bonjour! NexSupport est à votre service. Faites-moi savoir si vous avez des questions sur vos récentes **commandes** ou **remboursements** !",
        'de': "👋 Hallo! NexSupport ist für Sie da. Lassen Sie mich wissen, wenn Sie Fragen zu Ihren letzten **Bestellungen** oder **Rückerstattungen** haben!",
        'ja': "👋 こんにちは！NexSupportがお手伝いいたします。最近の**注文**や**返金**についてご質問がございましたら、お知らせください！"
    },
    "📦 I can certainly help check your order status. Could you please provide your **Order ID**? Standard delivery takes **3-5 business days**. You can also track your shipment here: `https://track.nexsupport.com/`": {
        'hi': "📦 मैं निश्चित रूप से आपके ऑर्डर की स्थिति जांचने में मदद कर सकता हूँ। क्या आप कृपया अपना **ऑर्डर आईडी** प्रदान कर सकते हैं? मानक वितरण में **3-5 व्यावसायिक दिन** लगते हैं। आप अपने शिपमेंट को यहां भी ट्रैक कर सकते हैं: `https://track.nexsupport.com/`",
        'es': "📦 Con gusto puedo ayudarte a verificar el estado de tu pedido. ¿Podrías proporcionar tu **ID de pedido**? La entrega estándar tarda de **3 a 5 días hábiles**. También puedes rastrear tu envío aquí: `https://track.nexsupport.com/`",
        'fr': "📦 Je peux certainement vous aider à vérifier le statut de votre commande. Pourriez-vous s'il vous plaît fournir votre **ID de commande**? La livraison standard prend **3 à 5 jours ouvrables**. Vous pouvez également suivre votre envoi ici: `https://track.nexsupport.com/`",
        'de': "📦 Ich kann Ihnen gerne helfen, Ihren Bestellstatus zu überprüfen. Könnten Sie bitte Ihre **Bestell-ID** angeben? Die Standardlieferung dauert **3-5 Werktage**. Sie können Ihre Sendung auch hier verfolgen: `https://track.nexsupport.com/`",
        'ja': "📦 注文ステータスの確認をお手伝いいたします。**注文ID**をご入力いただけますか？通常配送には**3〜5営業日**かかります。こちらから発送状況を追跡することもできます：`https://track.nexsupport.com/`"
    },
    "📦 Sure, let's check your shipment. Please share your **Order ID**! Once shipped, standard delivery takes **3-5 days**, and you will receive a tracking link via email.": {
        'hi': "📦 ज़रूर, आइए आपका शिपमेंट जांचें। कृपया अपना **ऑर्डर आईडी** साझा करें! एक बार शिप होने के बाद, मानक वितरण में **3-5 दिन** लगते हैं, और आपको ईमेल के माध्यम से एक ट्रैकिंग लिंक प्राप्त होगा।",
        'es': "📦 Claro, verifiquemos tu envío. ¡Por favor comparte tu **ID de pedido**! Una vez enviado, la entrega estándar tarda de **3 a 5 días** y recibirás un enlace de seguimiento por correo electrónico.",
        'fr': "📦 Bien sûr, vérifions votre envoi. Veuillez partager votre **ID de commande** ! Une fois expédiée, la livraison standard prend **3 à 5 jours** et vous recevrez un lien de suivi par e-mail.",
        'de': "📦 Sicher, lassen Sie uns Ihre Sendung überprüfen. Bitte teilen Sie Ihre **Bestell-ID** mit! Nach dem Versand dauert die Standardlieferung **3-5 Tage** und Sie erhalten einen Tracking-Link per E-Mail.",
        'ja': "📦 かしこまりました。発送状況を確認します。**注文ID**を教えてください。発送後、通常お届けには**3〜5日**かかります。また、メールで追跡リンクをお送りします。"
    },
    "💳 We offer a **30-day refund policy** for all products. If you are within this window, please provide your **Order ID** and the reason for return so I can initiate the refund.": {
        'hi': "💳 हम सभी उत्पादों के लिए **30 दिनों की रिफंड नीति** प्रदान करते हैं। यदि आप इस अवधि के भीतर हैं, तो कृपया अपना **ऑर्डर आईडी** और वापसी का कारण प्रदान करें ताकि मैं रिफंड शुरू कर सकूं।",
        'es': "💳 Ofrecemos una **política de reembolso de 30 días** para todos los productos. Si te encuentras dentro de este plazo, proporciona tu **ID de pedido** y el motivo de la devolución para que pueda iniciar el reembolso.",
        'fr': "💳 Nous offrons une **politique de remboursement de 30 jours** pour tous les produits. Si vous êtes dans ce délai, veuillez fournir votre **ID de commande** et le motif du retour afin que je puisse lancer le remboursement.",
        'de': "💳 Wir bieten eine **30-tägige Rückerstattungsrichtlinie** für alle Produkte an. Wenn Sie sich innerhalb dieses Zeitfensters befinden, geben Sie bitte Ihre **Bestell-ID** und den Grund für die Rückgabe an, damit ich die Rückerstattung einleiten kann.",
        'ja': "💳 すべての商品に対して**30日間の返金ポリシー**を提供しています。この期間内であれば、返金手続きを開始するために**注文ID**と返品理由をご提示ください。"
    },
    "💳 No worries! Refunds are fully supported within **30 days** of purchase. Please share your **Order ID** and we'll get that processed for you.": {
        'hi': "💳 कोई बात नहीं! खरीद के **30 दिनों** के भीतर रिफंड पूरी तरह से समर्थित है। कृपया अपना **ऑर्डर आईडी** साझा करें और हम इसे आपके लिए संसाधित कर देंगे।",
        'es': "💳 ¡No te preocupes! Los reembolsos son totalmente compatibles dentro de los **30 días** de la compra. Comparte tu **ID de pedido** y lo procesaremos por ti.",
        'fr': "💳 Ne vous inquiétez pas ! Les remboursements sont entièrement acceptés dans les **30 jours** suivant l'achat. Veuillez partager votre **ID de commande** et nous la traiterons pour vous.",
        'de': "💳 Keine Sorge! Rückerstattungen werden innerhalb von **30 Tagen** nach dem Kauf vollständig unterstützt. Bitte teilen Sie Ihre **Bestell-ID** mit und wir werden dies für Sie bearbeiten.",
        'ja': "💳 ご安心ください！ご購入後**30日以内**であれば返金が可能です。**注文ID**を教えていただければ、手続きを進めさせていただきます。"
    },
    "😤 I am truly sorry to hear that you are experiencing issues. I have recorded your complaint and escalated it to our high-priority support team. A manager will reach out within **2 hours**.": {
        'hi': "😤 मुझे यह सुनकर वास्तव में दुख हुआ कि आप समस्याओं का सामना कर रहे हैं। मैंने आपकी शिकायत दर्ज कर ली है और इसे हमारी उच्च-प्राथमिकता सहायता टीम को भेज दिया है। एक प्रबंधक **2 घंटे** के भीतर आपसे संपर्क करेगा।",
        'es': "😤 Lamento mucho escuchar que estás experimentando problemas. He registrado tu queja y la he derivado a nuestro equipo de soporte de alta prioridad. Un gerente se comunicará contigo en menos de **2 horas**.",
        'fr': "😤 Je suis vraiment désolé d'apprendre que vous rencontrez des problèmes. J'ai enregistré votre plainte et l'ai transmise à notre équipe d'assistance prioritaire. Un responsable vous contactera d'ici **2 heures**.",
        'de': "😤 Es tut mir wirklich leid zu hören, dass Sie Probleme haben. Ich habe Ihre Beschwerde aufgenommen und an unser Support-Team mit hoher Priorität weitergeleitet. Ein Manager wird sich innerhalb von **2 Stunden** bei Ihnen melden.",
        'ja': "😤 問題が発生しているとのこと、大変申し訳ございません。いただいた苦情を記録し、優先度の高いサポートチームにエスカレーションいたしました。マネージャーから**2時間以内**にご連絡いたします。"
    },
    "😤 I apologize for the frustration this has caused. I am escalating this immediately. Our premium support agents will contact you within **2 hours** to resolve this issue.": {
        'hi': "😤 इसके कारण हुई निराशा के लिए मैं क्षमा चाहता हूँ। मैं इसे तुरंत आगे बढ़ा रहा हूँ। हमारी प्रीमियम सहायता टीम इस मुद्दे को हल करने के लिए **2 घंटे** के भीतर आपसे संपर्क करेगी।",
        'es': "😤 Disculpa la frustración que esto ha causado. Estoy escalando esto inmediatamente. Nuestros agentes de soporte premium se comunicarán contigo dentro de **2 horas** para resolver este problema.",
        'fr': "😤 Je m'excuse pour la frustration que cela a causée. J'escalade cela immédiatement. Nos agents d'assistance premium vous contacteront d'ici **2 heures** pour résoudre ce problème.",
        'de': "😤 Ich entschuldige mich für den Frust, den dies verursacht hat. Ich leite dies sofort weiter. Unsere Premium-Support-Mitarbeiter werden sich innerhalb von **2 Stunden** mit Ihnen in Verbindung setzen, um das Problem zu lösen.",
        'ja': "😤 ご不便をおかけして大変申し訳ございません。すぐにエスカレーションいたします。問題解決のため、**2時間以内**にプレミアムサポート担当者からご連絡いたします。"
    },
    "🕐 NexSupport is open from **Monday to Friday: 9AM – 7PM IST** and **Saturday: 10AM – 4PM IST**. We are closed on Sundays.": {
        'hi': "🕐 नेक्ससपोर्ट **सोमवार से शुक्रवार: सुबह 9 बजे – शाम 7 बजे IST** और **शनिवार: सुबह 10 बजे – दोपहर 4 बजे IST** तक खुला रहता है। हम रविवार को बंद रहते हैं।",
        'es': "🕐 NexSupport está abierto de **lunes a viernes: 9:00 AM – 7:00 PM IST** y **sábados: 10:00 AM – 4:00 PM IST**. Los domingos estamos cerrados.",
        'fr': "🕐 NexSupport est ouvert du **lundi au vendredi: 9h00 – 19h00 IST** et le **samedi: 10h00 – 16h00 IST**. Nous sommes fermés le dimanche.",
        'de': "🕐 NexSupport ist von **Montag bis Freitag: 9:00 – 19:00 Uhr IST** und **Samstag: 10:00 – 16:00 Uhr IST** geöffnet. Sonntags haben wir geschlossen.",
        'ja': "🕐 NexSupportの営業時間は、**月曜日から金曜日：午前9時〜午後7時（IST）**、および**土曜日：午前10時〜午後4時（IST）**です。日曜日は休業日です。"
    },
    "🕐 Our support hours are **Mon-Fri 9:00 AM – 7:00 PM IST** and **Saturday 10:00 AM – 4:00 PM IST**. On Sundays, we are closed.": {
        'hi': "🕐 हमारे काम के घंटे **सोमवार-शुक्रवार सुबह 9:00 बजे – शाम 7:00 बजे IST** और **शनिवार सुबह 10:00 बजे – दोपहर 4:00 बजे IST** हैं। रविवार को हम बंद रहते हैं।",
        'es': "🕐 Horario de atención: **lun-vie 9:00 AM – 7:00 PM IST** y **sábados 10:00 AM – 4:00 PM IST**. Domingos cerrado.",
        'fr': "🕐 Nos heures d'assistance sont **lun-ven 9h00 – 19h00 IST** et **samedi 10h00 – 16h00 IST**. Le dimanche, nous sommes fermés.",
        'de': "🕐 Unsere Supportzeiten sind **Mo-Fr 9:00 – 17:00 Uhr IST** und **Samstag 10:00 – 16:00 Uhr IST**. Sonntags geschlossen.",
        'ja': "🕐 サポートの受付時間は、**月曜〜金曜 午前9:00〜午後7:00（IST）**、**土曜 午前10:00〜午後4:00（IST）**です。日曜日は休業です。"
    },
    "👋 Goodbye! Thank you for choosing NexSupport. Feel free to reach out if you need anything else. Have a wonderful day!": {
        'hi': "👋 अलविदा! नेक्ससपोर्ट चुनने के लिए धन्यवाद। यदि आपको किसी और चीज़ की आवश्यकता हो तो बेझिझक संपर्क करें। आपका दिन शुभ हो!",
        'es': "👋 ¡Adiós! Gracias por elegir NexSupport. No dudes en contactarnos si necesitas algo más. ¡Que tengas un excelente día!",
        'fr': "👋 Au revoir! Merci d'avoir choisi NexSupport. N'hésitez pas à nous contacter si vous avez besoin d'autre chose. Passez une excellente journée !",
        'de': "👋 Auf Wiedersehen! Vielen Dank, dass Sie sich für NexSupport entschieden haben. Melden Sie sich gerne, wenn Sie noch etwas benötigen. Haben Sie einen schönen Tag!",
        'ja': "👋 さようなら！NexSupportをご利用いただきありがとうございました。他にご不明な点がございましたら、お気軽にお問い合わせください。良い一日をお過ごしください！"
    },
    "👋 Thanks for chatting! I'm closing this session. Let me know if you need help in the future. Take care!": {
        'hi': "👋 बातचीत करने के लिए धन्यवाद! मैं यह सत्र बंद कर रहा हूँ। यदि आपको भविष्य में सहायता की आवश्यकता हो तो मुझे बताएं। अपना ख्याल रखें!",
        'es': "👋 ¡Gracias por chatear! Cierro esta sesión. Déjame saber si necesitas ayuda en el futuro. ¡Cuídate!",
        'fr': "👋 Merci pour cette discussion ! Je ferme cette session. Faites-moi savoir si vous avez besoin d'aide à l'avenir. Prenez soin de vous !",
        'de': "👋 Danke für das Gespräch! Ich beende diese Sitzung. Lassen Sie mich wissen, wenn Sie in Zukunft Hilfe benötigen. Passen Sie auf sich auf!",
        'ja': "👋 お話しいただきありがとうございました！セッションを終了します。また何かございましたら、いつでもお気軽にご連絡ください。お元気で！"
    },
    
    # Active Flow items
    "Action cancelled. Back to the main menu!": {
        'hi': "कार्रवाई रद्द कर दी गई। मुख्य मेनू पर वापस जाएं!",
        'es': "Acción cancelada. ¡Volver al menú principal!",
        'fr': "Action annulée. Retour au menu principal !",
        'de': "Aktion abgebrochen. Zurück zum Hauptmenü!",
        'ja': "操作はキャンセルされました。メインメニューに戻ります！"
    },
    
    # Warning/Error and Interactive flow messages
    "That doesn't look like a valid email address. Please enter a valid email (e.g. name@example.com):": {
        'hi': "यह एक मान्य ईमेल पता नहीं लग रहा है। कृपया एक मान्य ईमेल दर्ज करें (जैसे name@example.com):",
        'es': "Esa no parece ser una dirección de correo electrónico válida. Por favor, ingresa un correo válido (ej. nombre@ejemplo.com):",
        'fr': "Cela ne ressemble pas à une adresse e-mail valide. Veuillez saisir une adresse e-mail valide (ex. nom@exemple.com) :",
        'de': "Das sieht nicht nach einer gültigen E-Mail-Adresse aus. Bitte geben Sie eine gültige E-Mail-Adresse ein (z. B. name@example.com):",
        'ja': "有効なメールアドレスではないようです。有効なメールアドレスを入力してください（例：name@example.com）："
    },
    "That doesn't look like a valid Order ID.\n\nOrder IDs follow this format: **ORD-XXXXXX**\n(Example: **ORD-789012**)\n\nYou can find your Order ID in your confirmation email.": {
        'hi': "यह एक मान्य ऑर्डर आईडी नहीं लग रहा है।\n\nऑर्डर आईडी इस प्रारूप का पालन करते हैं: **ORD-XXXXXX**\n(उदाहरण: **ORD-789012**)\n\nआप अपने पुष्टिकरण ईमेल में अपना ऑर्डर आईडी पा सकते हैं।",
        'es': "Ese no parece ser un ID de pedido válido.\n\nLos ID de pedido siguen este formato: **ORD-XXXXXX**\n(Ejemplo: **ORD-789012**)\n\nPuedes encontrar tu ID de pedido en tu correo electrónico de confirmación.",
        'fr': "Cela ne ressemble pas à un ID de commande valide.\n\nLes ID de commande suivent ce format : **ORD-XXXXXX**\n(Exemple : **ORD-789012**)\n\nVous trouverez votre ID de commande dans votre e-mail de confirmation.",
        'de': "Das sieht nicht nach einer gültigen Bestell-ID aus.\n\nBestell-IDs haben folgendes Format: **ORD-XXXXXX**\n(Beispiel: **ORD-789012**)\n\nSie finden Ihre Bestell-ID in Ihrer Bestätigungs-E-Mail.",
        'ja': "有効な注文IDではないようです。\n\n注文IDは次の形式です：**ORD-XXXXXX**\n（例：**ORD-789012**）\n\n注文IDは確認メールに記載されています。"
    },
    "That doesn't look like a valid Order ID.\n\nPlease provide a valid Order ID (e.g., **ORD-789012**) to process your refund.": {
        'hi': "यह एक मान्य ऑर्डर आईडी नहीं लग रहा है।\n\nअपना रिफंड संसाधित करने के लिए कृपया एक मान्य ऑर्डर आईडी (जैसे, **ORD-789012**) प्रदान करें।",
        'es': "Ese no parece ser un ID de pedido válido.\n\nPor favor, proporciona un ID de pedido válido (ej., **ORD-789012**) para procesar tu reembolso.",
        'fr': "Cela ne ressemble pas à un ID de commande valide.\n\nVeuillez fournir un ID de commande valide (ex., **ORD-789012**) pour traiter votre remboursement.",
        'de': "Das sieht nicht nach einer gültigen Bestell-ID aus.\n\nBitte geben Sie eine gültige Bestell-ID an (z. B. **ORD-789012**), um Ihre Rückerstattung zu bearbeiten.",
        'ja': "有効な注文IDではないようです。\n\n返金を処理するには、有効な注文ID（例：**ORD-789012**）を入力してください。"
    },
    "📞 **Priority Support Escalation**\n\nI've escalated your issue regarding Order #8821 to a senior support representative. A live agent will call or email you in **less than 10 minutes** to resolve this.": {
        'hi': "📞 **प्राथमिकता सहायता वृद्धि**\n\nमैंने ऑर्डर #8821 के संबंध में आपकी समस्या एक वरिष्ठ सहायता प्रतिनिधि को भेज दी है। एक लाइव एजेंट इसे हल करने के लिए **10 मिनट से भी कम समय** में आपसे फोन या ईमेल पर संपर्क करेगा।",
        'es': "📞 **Escalación de Soporte de Prioridad**\n\nHe derivado tu problema con el Pedido #8821 a un representante de soporte senior. Un agente en vivo te llamará o enviará un correo electrónico en **menos de 10 minutos** para resolver esto.",
        'fr': "📞 **Escalade de l'assistance prioritaire**\n\nJ'ai transmis votre problème concernant la commande #8821 à un représentant de l'assistance senior. Un agent en direct vous appellera ou vous enverra un e-mail dans **moins de 10 minutes** pour résoudre ce problème.",
        'de': "📞 **Eskalation des Priority-Supports**\n\nIch habe Ihr Problem bezüglich Bestellung #8821 an einen leitenden Support-Mitarbeiter weitergeleitet. Ein Live-Mitarbeiter wird Sie in **weniger als 10 Minuten** anrufen oder Ihnen eine E-Mail senden, um das Problem zu lösen.",
        'ja': "📞 **優先サポートエスカレーション**\n\n注文番号8821に関するお客様の問題をシニアサポート担当者に報告しました。問題を解決するため、**10分以内**に担当者からお電話またはメールでご連絡いたします。"
    },
    "📍 **GPS Verification Request Initiated**\n\nI have contacted the courier to retrieve the exact GPS coordinates and time of the scan. I am also opening a priority dispute ticket for you. An agent will contact you shortly.": {
        'hi': "📍 **जीपीएस सत्यापन अनुरोध शुरू किया गया**\n\nसटीक जीपीएस निर्देशांक और स्कैन का समय प्राप्त करने के लिए मैंने कूरियर से संपर्क किया है। मैं आपके लिए एक प्राथमिकता विवाद टिकट भी खोल रहा हूँ। एक एजेंट जल्द ही आपसे संपर्क करेगा।",
        'es': "📍 **Solicitud de verificación de GPS iniciada**\n\nHe contactado al servicio de mensajería para obtener las coordenadas GPS exactas y la hora del escaneo. También abriré un ticket de disputa prioritaria para ti. Un agente te contactará pronto.",
        'fr': "📍 **Demande de vérification GPS initiée**\n\nJ'ai contacté le transporteur pour obtenir les coordonnées GPS exactes et l'heure du scan. J'ouvre également un ticket de litige prioritaire pour vous. Un agent vous contactera sous peu.",
        'de': "📍 **GPS-Verifizierungsanfrage initiiert**\n\nIch habe den Kurier kontaktiert, um die genauen GPS-Koordinaten und den Zeitpunkt des Scans abzurufen. Ich eröffne auch ein Ticket für eine bevorzugte Reklamation für Sie. Ein Mitarbeiter wird sich in Kürze mit Ihnen in Verbindung setzen.",
        'ja': "📍 **GPS確認リクエスト開始**\n\n配送業者に連絡し、スキャンの正確なGPS座標と時刻を取得しています。また、優先紛争チケットを発行しました。担当者から追跡のご連絡を差し上げます。"
    }
}

def translate_to_english(text):
    """
    Translates input text from any language to English.
    If text is already English, an Order ID, or a core command, returns it as-is.
    """
    if not text:
        return text

    cleaned = text.strip().lower()
    
    # Avoid translating Order IDs, numbers, or core keywords
    if re.match(r'^ord-\d+$', cleaned) or cleaned in ['cancel', 'back', 'menu', 'exit', '1', '2']:
        return text

    # Reverse lookup in local translation dictionary for instant offline lookup
    for eng_text, translations in LOCAL_TRANSLATIONS.items():
        for lang, trans_text in translations.items():
            if trans_text.strip().lower() == cleaned:
                return eng_text

    key = os.getenv('GEMINI_API_KEY')
    if not key:
        return text

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
    headers = {
        'Content-Type': 'application/json'
    }

    prompt = (
        "Translate the following user message to English. "
        "If it is already in English, return it exactly as is. "
        "Return ONLY the translated English text, with no extra explanation, intro, or quotes.\n"
        f"Message: {text}"
    )

    body = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "maxOutputTokens": 1000,
            "temperature": 0.1
        }
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=10)
        if response.status_code == 200:
            data = response.json()
            translated = data['candidates'][0]['content']['parts'][0]['text'].strip()
            if (translated.startswith('"') and translated.endswith('"')) or (translated.startswith("'") and translated.endswith("'")):
                translated = translated[1:-1].strip()
            return translated
    except Exception as e:
        print(f"Translation to English failed: {e}")
    return text

DAY_MAP = {
    'hi': {
        'Mon-Fri': 'सोम-शुक्र',
        'Sat-Sun': 'शनि-रवि',
        'Monday to Friday': 'सोमवार से शुक्रवार',
        'Monday-Friday': 'सोमवार-शुक्रवार',
        'Monday': 'सोमवार',
        'Friday': 'शुक्रवार',
        'Saturday': 'शनिवार',
        'Sunday': 'रविवार',
        'Mon': 'सोम',
        'Fri': 'शुक्र',
        'Sat': 'शनि',
        'Sun': 'रवि',
        'Closed': 'बंद',
        'closed': 'बंद',
        'Operating Hours': 'सपोर्ट के घंटे',
    },
    'es': {
        'Mon-Fri': 'Lun-Vie',
        'Sat-Sun': 'Sáb-Dom',
        'Monday to Friday': 'lunes a viernes',
        'Monday-Friday': 'lunes-viernes',
        'Monday': 'lunes',
        'Friday': 'viernes',
        'Saturday': 'sábado',
        'Sunday': 'domingo',
        'Mon': 'Lun',
        'Fri': 'Vie',
        'Sat': 'Sáb',
        'Sun': 'Dom',
        'Closed': 'Cerrado',
        'closed': 'cerrado',
        'Operating Hours': 'Horario de atención',
    },
    'fr': {
        'Mon-Fri': 'Lun-Ven',
        'Sat-Sun': 'Sam-Dim',
        'Monday to Friday': 'lundi au vendredi',
        'Monday-Friday': 'lundi-vendredi',
        'Monday': 'lundi',
        'Friday': 'vendredi',
        'Saturday': 'samedi',
        'Sunday': 'dimanche',
        'Mon': 'Lun',
        'Fri': 'Ven',
        'Sat': 'Sam',
        'Sun': 'Dim',
        'Closed': 'Fermé',
        'closed': 'fermé',
        'Operating Hours': "Heures d'ouverture",
    },
    'de': {
        'Mon-Fri': 'Mo-Fr',
        'Sat-Sun': 'Sa-So',
        'Monday to Friday': 'Montag bis Freitag',
        'Monday-Friday': 'Montag-Freitag',
        'Monday': 'Montag',
        'Friday': 'Freitag',
        'Saturday': 'Samstag',
        'Sunday': 'Sonntag',
        'Mon': 'Mo',
        'Fri': 'Fr',
        'Sat': 'Sa',
        'Sun': 'So',
        'Closed': 'Geschlossen',
        'closed': 'geschlossen',
        'Operating Hours': 'Supportzeiten',
    },
    'ja': {
        'Mon-Fri': '月-金',
        'Sat-Sun': '土-日',
        'Monday to Friday': '月曜日から金曜日',
        'Monday-Friday': '月曜日-金曜日',
        'Monday': '月曜日',
        'Friday': '金曜日',
        'Saturday': '土曜日',
        'Sunday': '日曜日',
        'Mon': '月',
        'Fri': '金',
        'Sat': '土',
        'Sun': '日',
        'Closed': '休業日',
        'closed': '休業日',
        'Operating Hours': '営業時間',
    }
}

def parse_time_str(time_str):
    m = re.match(r'^(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?$', time_str.strip())
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2)) if m.group(2) else 0
    period = m.group(3).upper() if m.group(3) else None
    return hour, minute, period

def format_time_for_lang(hour, minute, period, lang):
    if lang == 'hi':
        time_part = f"{hour}:{minute:02d}" if minute > 0 else f"{hour}"
        if period == 'AM':
            return f"सुबह {time_part} बजे"
        elif period == 'PM':
            if hour == 12 or (hour >= 1 and hour <= 4):
                return f"दोपहर {time_part} बजे"
            else:
                return f"शाम {time_part} बजे"
        return f"{time_part} बजे"
    elif lang == 'ja':
        time_part = f"{hour}:{minute:02d}" if minute > 0 else f"{hour}時"
        if period == 'AM':
            return f"午前{hour}:{minute:02d}" if minute > 0 else f"午前{hour}時"
        elif period == 'PM':
            return f"午後{hour}:{minute:02d}" if minute > 0 else f"午後{hour}時"
        return time_part
    elif lang == 'fr':
        h24 = hour
        if period == 'PM' and hour < 12:
            h24 += 12
        elif period == 'AM' and hour == 12:
            h24 = 0
        return f"{h24}h{minute:02d}" if minute > 0 else f"{h24}h"
    elif lang == 'de':
        h24 = hour
        if period == 'PM' and hour < 12:
            h24 += 12
        elif period == 'AM' and hour == 12:
            h24 = 0
        return f"{h24}:{minute:02d} Uhr" if minute > 0 else f"{h24}:00 Uhr"
    elif lang == 'es':
        time_part = f"{hour}:{minute:02d}" if minute > 0 else f"{hour}"
        if period:
            return f"{time_part} {period}"
        return time_part
    else:
        time_part = f"{hour}:{minute:02d}" if minute > 0 else f"{hour}"
        if period:
            return f"{time_part} {period}"
        return time_part

VALID_DAYS = {
    'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    'mo', 'tu', 'we', 'th', 'fr', 'sa', 'so',
    'mon-fri', 'sat-sun', 'monday to friday', 'monday-friday', 'saturday-sunday'
}

def is_valid_day_part(day_part):
    cleaned = day_part.lower().strip()
    if cleaned in VALID_DAYS:
        return True
    parts = re.split(r'\s*(?:-|–|to)\s*', cleaned)
    if len(parts) == 2 and parts[0] in VALID_DAYS and parts[1] in VALID_DAYS:
        return True
    return False

def translate_hours_text(text, target_lang):
    if not text or not target_lang or target_lang == 'en':
        return text

    cleaned = text.strip()
    
    if target_lang in DAY_MAP and cleaned in DAY_MAP[target_lang]:
        return DAY_MAP[target_lang][cleaned]
        
    day_prefix_match = re.match(
        r'^([A-Za-z]+(?:\s*(?:-|–|to)\s*[A-Za-z]+)?)\s*[:\s]\s*(.*)$', 
        cleaned
    )
    if not day_prefix_match:
        return None

    day_part = day_prefix_match.group(1).strip()
    if not is_valid_day_part(day_part):
        return None
    time_part = day_prefix_match.group(2).strip()

    translated_day = day_part
    if target_lang in DAY_MAP:
        lang_day_map = DAY_MAP[target_lang]
        if day_part in lang_day_map:
            translated_day = lang_day_map[day_part]
        else:
            parts = re.split(r'\s*(?:-|–|to)\s*', day_part)
            if len(parts) == 2:
                d1 = lang_day_map.get(parts[0], parts[0])
                d2 = lang_day_map.get(parts[1], parts[1])
                sep = '-'
                translated_day = f"{d1}{sep}{d2}"

    translated_time = time_part
    if time_part.lower() == 'closed':
        if target_lang in DAY_MAP and 'Closed' in DAY_MAP[target_lang]:
            translated_time = DAY_MAP[target_lang]['Closed']
    else:
        time_range_match = re.match(
            r'^([^–-]+)\s*[–-]\s*([^–-]+?)(?:\s*(IST))?$',
            time_part
        )
        if time_range_match:
            start_str = time_range_match.group(1).strip()
            end_str = time_range_match.group(2).strip()
            tz_str = time_range_match.group(3)
            
            start_parsed = parse_time_str(start_str)
            end_parsed = parse_time_str(end_str)
            
            if start_parsed and end_parsed:
                st_h, st_m, st_p = start_parsed
                et_h, et_m, et_p = end_parsed
                
                if not st_p and et_p:
                    if st_h >= et_h:
                        st_p = 'AM'
                    else:
                        st_p = et_p
                
                st_formatted = format_time_for_lang(st_h, st_m, st_p or 'AM', target_lang)
                et_formatted = format_time_for_lang(et_h, et_m, et_p or 'PM', target_lang)
                
                sep = " - "
                if target_lang == 'hi':
                    sep = " – "
                elif target_lang == 'ja':
                    sep = "〜"
                
                translated_time = f"{st_formatted}{sep}{et_formatted}"
                if tz_str:
                    if target_lang == 'ja':
                        translated_time = f"{translated_time}（{tz_str}）"
                    else:
                        translated_time = f"{translated_time} {tz_str}"

    if target_lang == 'ja':
        return f"{translated_day}：{translated_time}"
    else:
        return f"{translated_day}: {translated_time}"

def translate_templated_message(text, target_lang):
    if not text or not target_lang or target_lang == 'en':
        return None

    cleaned = text.strip()

    # Pattern 1: Thanks, **{user_name}**! Now, please enter your email address so we can associate it with this order.
    m = re.match(
        r'^Thanks,\s+\*\*(.*?)\*\*!\s+Now,\s+please\s+enter\s+your\s+email\s+address\s+so\s+we\s+can\s+associate\s+it\s+with\s+this\s+order\.$',
        cleaned,
        re.DOTALL
    )
    if m:
        user_name = m.group(1)
        templates = {
            'hi': "धन्यवाद, **{user_name}**! अब, कृपया अपना ईमेल पता दर्ज करें ताकि हम इसे इस ऑर्डर से जोड़ सकें।",
            'es': "¡Gracias, **{user_name}**! Ahora, por favor ingresa tu dirección de correo electrónico para que podamos asociarla con este pedido.",
            'fr': "Merci, **{user_name}** ! Maintenant, veuillez entrer votre adresse e-mail afin que nous puissions l'associer à cette commande.",
            'de': "Danke, **{user_name}**! Bitte geben Sie jetzt Ihre E-Mail-Adresse ein, damit wir sie dieser Bestellung zuordnen können.",
            'ja': "**{user_name}**様、ありがとうございます！この注文に関連付けるため、メールアドレスを入力してください。"
        }
        return templates.get(target_lang, text).format(user_name=user_name)

    # Pattern 2: I found Order **{extracted_id}**. To retrieve your order details, please tell me your full name.
    m = re.match(
        r'^I\s+found\s+Order\s+\*\*(ORD-\d+)\*\*\.\s+To\s+retrieve\s+your\s+order\s+details,\s+please\s+tell\s+me\s+your\s+full\s+name\.$',
        cleaned,
        re.DOTALL
    )
    if m:
        order_id = m.group(1)
        templates = {
            'hi': "मुझे ऑर्डर **{order_id}** मिला। आपके ऑर्डर का विवरण प्राप्त करने के लिए, कृपया मुझे अपना पूरा नाम बताएं।",
            'es': "Encontré el pedido **{order_id}**. Para recuperar los detalles de tu pedido, por favor dime tu nombre completo.",
            'fr': "J'ai trouvé la commande **{order_id}**. Pour récupérer les détails de votre commande, veuillez me donner votre nom complet.",
            'de': "Ich habe die Bestellung **{order_id}** gefunden. Um Ihre Bestelldetails abzurufen, nennen Sie mir bitte Ihren vollständigen Namen.",
            'ja': "注文**{order_id}**が見つかりました。注文の詳細を取得するには、フルネームを教えてください。"
        }
        return templates.get(target_lang, text).format(order_id=order_id)

    # Pattern 3: That Order ID (**{extracted_id}**) could not be found in our database. Please double check the ID and try again.
    m = re.match(
        r'^That\s+Order\s+ID\s+\(\*\*(ORD-\d+)\*\*\)\s+could\s+not\s+be\s+found\s+in\s+our\s+database\.\s+Please\s+double\s+check\s+the\s+ID\s+and\s+try\s+again\.$',
        cleaned,
        re.DOTALL
    )
    if m:
        order_id = m.group(1)
        templates = {
            'hi': "वह ऑर्डर आईडी (**{order_id}**) हमारे डेटाबेस में नहीं मिली। कृपया आईडी की दोबारा जांच करें और पुनः प्रयास करें।",
            'es': "Ese ID de pedido (**{order_id}**) no se pudo encontrar en nuestra base de datos. Por favor, verifícalo e inténtalo de nuevo.",
            'fr': "Cet ID de commande (**{order_id}**) est introuvable dans notre base de données. Veuillez vérifier l'identifiant et réessayer.",
            'de': "Diese Bestell-ID (**{order_id}**) konnte in unserer Datenbank nicht gefunden werden. Bitte überprüfen Sie die ID und versuchen Sie es erneut.",
            'ja': "その注文ID（**{order_id}**）はデータベース内に見つかりませんでした。IDを再度ご確認の上、もう一度お試しください。"
        }
        return templates.get(target_lang, text).format(order_id=order_id)

    # Pattern 4 & 5: 📋 **Order ID Retrieved!**\n\nYour active Order ID is: `{new_id}`\n\nYou can now copy and paste this ID or type it to track this order / request a refund.
    m = re.match(
        r'^📋\s+\*\*Order\s+ID\s+Retrieved!\*\*\n\nYour\s+active\s+Order\s+ID\s+is:\s+`?(ORD-\d+)`?\n\nYou\s+can\s+now\s+copy\s+and\s+paste\s+this\s+ID\s+or\s+type\s+it\s+to\s+(track\s+this\s+order|request\s+a\s+refund)\.$',
        cleaned
    )
    if m:
        order_id = m.group(1)
        action = m.group(2)
        if 'refund' in action:
            templates = {
                'hi': "📋 **ऑर्डर आईडी प्राप्त हुई!**\n\nआपकी सक्रिय ऑर्डर आईडी है: `{order_id}`\n\nअब आप इस आईडी को कॉपी और पेस्ट कर सकते हैं या रिफंड का अनुरोध करने के लिए इसे टाइप कर सकते हैं।",
                'es': "📋 **¡ID de pedido recuperado!**\n\nTu ID de pedido activo es: `{order_id}`\n\nAhora puedes copiar y pegar este ID o escribirlo para solicitar un reembolso.",
                'fr': "📋 **ID de commande récupéré !**\n\nVotre ID de commande actif est : `{order_id}`\n\nVous pouvez maintenant copier et coller cet ID ou le saisir pour demander un remboursement.",
                'de': "📋 **Bestell-ID abgerufen!**\n\nIhre aktive Bestell-ID lautet: `{order_id}`\n\nSie können diese ID nun kopieren und einfügen oder eingeben, um eine Rückerstattung zu beantragen.",
                'ja': "📋 **注文IDを取得しました！**\n\n有効な注文IDは：`{order_id}`\n\nこのIDをコピー＆ペーストするか、入力して返金をリクエストできます。"
            }
        else:
            templates = {
                'hi': "📋 **ऑर्डर आईडी प्राप्त हुई!**\n\nआपकी सक्रिय ऑर्डर आईडी है: `{order_id}`\n\nअब आप इस आईडी को कॉपी और पेस्ट कर सकते हैं या इस ऑर्डर को ट्रैक करने के लिए इसे टाइप कर सकते हैं।",
                'es': "📋 **¡ID de pedido recuperado!**\n\nTu ID de pedido activo es: `{order_id}`\n\nAhora puedes copiar y pegar este ID o escribirlo para rastrear este pedido.",
                'fr': "📋 **ID de commande récupéré !**\n\nVotre ID de commande actif est : `{order_id}`\n\nVous pouvez maintenant copier et coller cet ID ou le saisir pour suivre cette commande.",
                'de': "📋 **Bestell-ID abgerufen!**\n\nIhre aktive Bestell-ID lautet: `{order_id}`\n\nSie können diese ID nun kopieren und einfügen oder eingeben, um diese Bestellung zu verfolgen.",
                'ja': "📋 **注文IDを取得しました！**\n\n有効な注文IDは：`{order_id}`\n\nこのIDをコピー＆ペーストするか、入力して注文を追跡できます。"
            }
        return templates.get(target_lang, text).format(order_id=order_id)

    # Pattern 6: 💳 **Refund Initiated for Order {order['id']}** ...
    m = re.match(
        r'^💳\s+\*\*Refund\s+Initiated\s+for\s+Order\s+(ORD-\d+)\*\*\n\nCustomer:\s+\*\*(.*?)\*\*\s+\((.*?)\)\n\nWe\s+have\s+successfully\s+initiated\s+a\s+refund\s+of\s+\*\*(.*?)\*\*\s+for\s+your\s+\*\*(.*?)\*\*\.\n\nThe\s+funds\s+should\s+appear\s+back\s+in\s+your\s+account\s+within\s+\*\*3[–-]5\s+business\s+days\*\*\.$',
        cleaned,
        re.DOTALL
    )
    if m:
        order_id, customer_name, email, price, item_name = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        templates = {
            'hi': "💳 **ऑर्डर {order_id} के लिए रिफंड शुरू किया गया**\n\nग्राहक: **{customer_name}** ({email})\n\nहमने आपके **{item_name}** के लिए **{price}** का रिफंड सफलतापूर्वक शुरू कर दिया है।\n\nराशि **3–5 व्यावसायिक दिनों** के भीतर आपके खाते में वापस आ जानी चाहिए।",
            'es': "💳 **Reembolso iniciado para el pedido {order_id}**\n\nCliente: **{customer_name}** ({email})\n\nHemos iniciado con éxito un reembolso de **{price}** para tu **{item_name}**.\n\nLos fondos deberían aparecer en tu cuenta dentro de **3 a 5 días hábiles**.",
            'fr': "💳 **Remboursement initié pour la commande {order_id}**\n\nClient : **{customer_name}** ({email})\n\nNous avons initié avec succès un remboursement de **{price}** pour votre **{item_name}**.\n\nLes fonds devraient apparaître sur votre compte sous **3 à 5 jours ouvrables**.",
            'de': "💳 **Rückerstattung für Bestellung {order_id} eingeleitet**\n\nKunde: **{customer_name}** ({email})\n\nWir haben erfolgreich eine Rückerstattung von **{price}** für Ihre **{item_name}** eingeleitet.\n\nDas Geld sollte innerhalb von **3–5 Werktagen** wieder auf Ihrem Konto eingehen.",
            'ja': "💳 **注文{order_id}の返金手続きを開始しました**\n\n顧客：**{customer_name}** ({email})\n\n**{item_name}**の**{price}**の返金手続きが正常に開始されました。\n\n資金は**3〜5営業日**以内にアカウントに戻るはずです。"
        }
        return templates.get(target_lang, text).format(order_id=order_id, customer_name=customer_name, email=email, price=price, item_name=item_name)

    # Pattern 7: 💳 **Refund Options for Order {order_id}** ...
    m = re.match(
        r'^💳\s+\*\*Refund\s+Options\s+for\s+Order\s+(ORD-\d+)\*\*\n\nCustomer:\s+\*\*(.*?)\*\*\s+\((.*?)\)\n\nSince\s+your\s+package\s+was\s+marked\s+delivered\s+but\s+not\s+received,\s+we\s+can:\n1\.\s+\*\*Re-ship\*\*\s+the\s+(.*?)\s+immediately\.\n2\.\s+Issue\s+a\s+\*\*full\s+refund\s+of\s+(.*?)\*\*\s+back\s+to\s+your\s+original\s+payment\s+method\.\n\nWould\s+you\s+like\s+me\s+to\s+process\s+a\s+full\s+refund\?$',
        cleaned,
        re.DOTALL
    )
    if m:
        order_id, customer_name, email, item_name, price = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        templates = {
            'hi': "💳 **ऑर्डर {order_id} के लिए रिफंड के विकल्प**\n\nग्राहक: **{customer_name}** ({email})\n\nचूंकि आपका पैकेज डिलीवर चिह्नित किया गया था लेकिन प्राप्त नहीं हुआ, हम कर सकते हैं:\n1. तुरंत {item_name} को **दोबारा भेजें**।\n2. आपके मूल भुगतान साधन पर **{price} का पूरा रिफंड** जारी करें।\n\nक्या आप चाहते हैं कि मैं पूरा रिफंड संसाधित करूं?",
            'es': "💳 **Opciones de reembolso para el pedido {order_id}**\n\nCliente: **{customer_name}** ({email})\n\nDado que tu paquete se marcó como entregado pero no se recibió, podemos:\n1. **Volver a enviar** el {item_name} de inmediato.\n2. Emitir un **reembolso completo de {price}** a tu método de pago original.\n\n¿Te gustaría que procese un reembolso completo?",
            'fr': "💳 **Options de remboursement pour la commande {order_id}**\n\nClient : **{customer_name}** ({email})\n\nPuisque votre colis a été marqué comme livré mais non reçu, nous pouvons :\n1. **Réexpédier** le {item_name} immédiatement.\n2. Émettre un **remboursement complet de {price}** sur votre mode de paiement d'origine.\n\nSouhaitez-vous que je procède à un remboursement complet ?",
            'de': "💳 **Rückerstattungsoptionen für Bestellung {order_id}**\n\nKunde: **{customer_name}** ({email})\n\nDa Ihr Paket als zugestellt markiert, aber nicht erhalten wurde, können wir:\n1. Das {item_name} sofort **erneut versenden**.\n2. Eine **vollständige Rückerstattung von {price}** auf Ihre ursprüngliche Zahlungsmethode veranlassen.\n\nMöchten Sie, dass ich eine vollständige Rückerstattung veranlasse?",
            'ja': "💳 **注文{order_id}の返金オプション**\n\n顧客：**{customer_name}** ({email})\n\nパッケージは配達済みとマークされていますが受け取られていないため、以下が可能です：\n1. すぐに{item_name}を**再発送**する。\n2. 元のお支払い方法に**{price}の全額返金**を発行する。\n\n全額返金を処理しますか？"
        }
        return templates.get(target_lang, text).format(order_id=order_id, customer_name=customer_name, email=email, price=price, item_name=item_name)

    # Pattern 8: 📦 **Replacement Order Confirmed** ...
    m = re.match(
        r'^📦\s+\*\*Replacement\s+Order\s+Confirmed\*\*\n\nWe\s+have\s+successfully\s+initiated\s+a\s+replacement\s+order\s+for\s+your\s+\*\*(.*?)\*\*\s+\(Order\s+(ORD-\d+)\)\.\n(?:A|a)\s+new\s+confirmation\s+email\s+with\s+tracking\s+details\s+will\s+be\s+sent\s+to\s+you\s+shortly\.$',
        cleaned,
        re.DOTALL
    )
    if m:
        item_name, order_id = m.group(1), m.group(2)
        templates = {
            'hi': "📦 **प्रतिस्थापन ऑर्डर की पुष्टि की गई**\n\nहमने आपके **{item_name}** (ऑर्डर {order_id}) के लिए सफलतापूर्वक एक प्रतिस्थापन ऑर्डर शुरू कर दिया है।\n\nट्रैकिंग विवरण के साथ एक नया पुष्टिकरण ईमेल जल्द ही आपको भेजा जाएगा।",
            'es': "📦 **Orden de reemplazo confirmada**\n\nHemos iniciado con éxito un pedido de reemplazo para tu **{item_name}** (Pedido {order_id}).\n\nPronto se te enviará un nuevo correo electrónico de confirmación con los detalles de seguimiento.",
            'fr': "📦 **Commande de remplacement confirmée**\n\nNous avons initié avec succès une commande de remplacement pour votre **{item_name}** (Commande {order_id}).\n\nUn nouvel e-mail de confirmation avec les détails de suivi vous sera envoyé sous peu.",
            'de': "📦 **Ersatzbestellung bestätigt**\n\nWir haben erfolgreich eine Ersatzlieferung für Ihre **{item_name}** (Bestellung {order_id}) veranlasst.\n\nEine neue Bestätigungs-E-Mail mit Sendungsverfolgungsdetails wird Ihnen in Kürze zugesandt.",
            'ja': "📦 **交換注文が確定しました**\n\n**{item_name}**（注文 {order_id}）の交換注文が正常に開始されました。\n\n追跡詳細を含む新しい確認メールがまもなく送信されます。"
        }
        return templates.get(target_lang, text).format(item_name=item_name, order_id=order_id)

    # Pattern 9: 💳 **Refund Initiated** ...
    m = re.match(
        r'^💳\s+\*\*Refund\s+Initiated\*\*\n\nWe\s+have\s+successfully\s+initiated\s+a\s+full\s+refund\s+of\s+\*\*(.*?)\*\*\s+for\s+your\s+\*\*(.*?)\*\*\.\n(?:The\s+credit\s+will\s+appear|The\s+funds\s+should\s+appear)(?:\s+back\s+)?on\s+your\s+(?:account|original\s+payment\s+method)\s+within\s+\*\*3[-–]5\s+business\s+days\*\*\.$',
        cleaned,
        re.DOTALL
    )
    if m:
        price, item_name = m.group(1), m.group(2)
        templates = {
            'hi': "💳 **रिफंड शुरू किया गया**\n\nहमने आपके **{item_name}** के लिए **{price}** का पूरा रिफंड सफलतापूर्वक शुरू कर दिया है।\n\nक्रेडिट **3-5 व्यावसायिक दिनों** के भीतर आपके खाते में दिखाई देगा।",
            'es': "💳 **Reembolso iniciado**\n\nHemos iniciado con éxito un reembolso completo de **{price}** por tu **{item_name}**.\n\nEl crédito aparecerá en tu cuenta en un plazo de **3 a 5 días hábiles**.",
            'fr': "💳 **Remboursement initié**\n\nNous avons initié avec succès un remboursement complet de **{price}** pour votre **{item_name}**.\n\nLe crédit apparaîtra sur votre compte sous **3 à 5 jours ouvrables**.",
            'de': "💳 **Rückerstattung eingeleitet**\n\nWir haben erfolgreich eine vollständige Rückerstattung von **{price}** für Ihre **{item_name}** eingeleitet.\n\nDie Gutschrift wird innerhalb von **3-5 Werktagen** auf Ihrem Konto eingehen.",
            'ja': "💳 **返金手続きを開始しました**\n\n**{item_name}**の**{price}**の全額返金が正常に開始されました。\n\nクレジットは**3〜5営業日**以内にアカウントに反映されます。"
        }
        return templates.get(target_lang, text).format(price=price, item_name=item_name)

    # Pattern 10: ORD-8821 Hello message
    m = re.match(
        r'^Hello,\s+\*\*(.*?)\*\*\s+\((.*?)\)!\s+I\s+understand\s+your\s+concern\s+regarding\s+\*\*Order\s+#8821\*\*\.\s+I\'ve\s+looked\s+into\s+the\s+tracking\s+logs\s+for\s+you\.\n\nAccording\s+to\s+our\s+detailed\s+dispatch\s+records:\n\n\*\s+The\s+package\s+was\s+marked\s+delivered\s+at\s+\*\*9:45\s+AM\*\*\.\n\*\s+Location:\s+\*\*Secured\s+Parcel\s+Locker\s+#12\*\*\.\n\*\s+The\s+signature\s+was\s+provided\s+by\s+\*\*\"Front\s+Desk\s+Personnel\"\*\*\.\n\nWould\s+you\s+like\s+me\s+to\s+initiate\s+a\s+\*\*GPS\s+verification\s+request\*\*\s+with\s+the\s+courier\s+or\s+contact\s+your\s+building\s+management\s+directly\?$',
        cleaned,
        re.DOTALL
    )
    if m:
        user_name, email = m.group(1), m.group(2)
        templates = {
            'hi': "नमस्ते, **{user_name}** ({email})! मैं **ऑर्डर #8821** के संबंध में आपकी चिंता समझता हूँ। मैंने आपके लिए ट्रैकिंग लॉग्स देखे हैं।\n\nहमारे विस्तृत प्रेषण रिकॉर्ड के अनुसार:\n\n* पैकेज **सुबह 9:45 बजे** वितरित चिह्नित किया गया था।\n* स्थान: **सुरक्षित पार्सल लॉकर #12**।\n* हस्ताक्षर **\"फ्रंट डेस्क कर्मियों\"** द्वारा प्रदान किए गए थे।\n\nक्या आप चाहते हैं कि मैं कूरियर के साथ **जीपीएस सत्यापन अनुरोध** शुरू करूँ या सीधे आपके भवन प्रबंधन से संपर्क करूँ?",
            'es': "¡Hola, **{user_name}** ({email})! Entiendo tu preocupación con respecto al **Pedido #8821**. He revisado los registros de seguimiento por ti.\n\nDe acuerdo con nuestros registros detallados de despacho:\n\n* El paquete fue marcado como entregado a las **9:45 AM**.\n* Ubicación: **Casillero de paquetes asegurado #12**.\n* La firma fue proporcionada por el **\"Personal de recepción\"**.\n\n¿Te gustaría que inicie una **solicitud de verificación de GPS** con el servicio de mensajería o que me comunique directamente con la administración de tu edificio?",
            'fr': "Bonjour, **{user_name}** ({email}) ! Je comprends votre préoccupation concernant la **commande #8821**. J'ai examiné les journaux de suivi pour vous.\n\nSelon nos registres d'expédition détaillés :\n\n* Le colis a été marqué comme livré à **9h45**.\n* Emplacement : **Casier à colis sécurisé n°12**.\n* La signature a été fournie par le **« Personnel de réception »**.\n\nSouhaitez-vous que je lance une **demande de vérification GPS** auprès du transporteur ou que je contacte directement la gestion de votre immeuble ?",
            'de': "Hallo, **{user_name}** ({email})! Ich verstehe Ihre Sorge bezüglich **Bestellung #8821**. Ich habe mir die Sendungsverfolgungsprotokolle für Sie angesehen.\n\nLaut unseren detaillierten Versandunterlagen:\n\n* Das Paket wurde um **9:45 Uhr** als zugestellt markiert.\n* Ort: **Sicheres Paketschließfach #12**.\n* Die Unterschrift wurde vom **„Personal an der Rezeption“** geleistet.\n\nMöchten Sie, dass ich eine **GPS-Verifizierungsanfrage** beim Kurier einleite oder mich direkt an Ihre Hausverwaltung wende?",
            'ja': "こんにちは、**{user_name}** ({email})様！**注文番号 8821**に関するご懸念は理解いたしました。追跡ログを確認しました。\n\n詳細な発送記録によると：\n\n* パッケージは**午前9:45**に配達完了とマークされています。\n* 場所：**宅配ロッカー #12**。\n* 署名は**「フロントデスク担当者」**によって提供されました。\n\n配送業者へ**GPS確認リクエスト**を開始するか、またはビルの管理会社へ直接問い合わせますか？"
        }
        return templates.get(target_lang, text).format(user_name=user_name, email=email)

    # Pattern 11: Fallback Order Status Info Block
    m = re.match(
        r'^📦\s+\*\*Order\s+(ORD-\d+)\*\*\n\nCustomer:\s*(.*?)\s*\((.*?)\)\nStatus:\s*(.*?)\nItem:\s*(.*?)\nPrice:\s*(.*?)(?:\nETA:\s*(.*?))?$',
        cleaned,
        re.DOTALL
    )
    if m:
        order_id, customer_name, email, status, item_name, price, eta = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6), m.group(7)
        status_map = {
            'hi': {'delivered': 'वितरित', 'shipped': 'भेजा गया', 'in transit': 'मार्ग में', 'processing': 'प्रसंस्करण', 'active dispute': 'सक्रिय विवाद'},
            'es': {'delivered': 'entregado', 'shipped': 'enviado', 'in transit': 'en tránsito', 'processing': 'procesando', 'active dispute': 'disputa activa'},
            'fr': {'delivered': 'livré', 'shipped': 'expédié', 'in transit': 'en cours de livraison', 'processing': 'en cours de traitement', 'active dispute': 'litige actif'},
            'de': {'delivered': 'zugestellt', 'shipped': 'versandt', 'in transit': 'unterwegs', 'processing': 'in bearbeitung', 'active dispute': 'aktive reklamation'},
            'ja': {'delivered': '配達済み', 'shipped': '発送済み', 'in transit': '輸送中', 'processing': '処理中', 'active dispute': '有効な紛争'}
        }
        trans_status = status.lower().strip()
        if target_lang in status_map and trans_status in status_map[target_lang]:
            trans_status = status_map[target_lang][trans_status]
        else:
            trans_status = status
            
        labels = {
            'hi': ('ऑर्डर', 'ग्राहक', 'स्थिति', 'उत्पाद', 'कीमत', 'अनुमानित समय (ETA)'),
            'es': ('Pedido', 'Cliente', 'Estado', 'Artículo', 'Precio', 'ETA'),
            'fr': ('Commande', 'Client', 'Statut', 'Article', 'Prix', 'ETA'),
            'de': ('Bestellung', 'Kunde', 'Status', 'Artikel', 'Preis', 'ETA'),
            'ja': ('注文', '顧客', 'ステータス', '商品', '価格', '配送予定（ETA）')
        }
        lbl_order, lbl_cust, lbl_stat, lbl_item, lbl_price, lbl_eta = labels.get(target_lang, ('Order', 'Customer', 'Status', 'Item', 'Price', 'ETA'))
        
        lines = [
            f"📦 **{lbl_order} {order_id}**",
            "",
            f"{lbl_cust}: {customer_name} ({email})",
            f"{lbl_stat}:  {trans_status}",
            f"{lbl_item}:    {item_name}",
            f"{lbl_price}:   {price}"
        ]
        if eta:
            lines.append(f"{lbl_eta}:     {eta}")
        return "\n".join(lines)

    return None

def translate_to_language(text, target_lang):
    """
    Translates the given text into target_lang using local dictionary or Gemini fallback.
    """
    if not text or not target_lang or target_lang == 'en':
        return text

    # Try local dictionary first
    if text in LOCAL_TRANSLATIONS:
        translations = LOCAL_TRANSLATIONS[text]
        if target_lang in translations:
            return translations[target_lang]

    # Try to clean keys for spacing/newlines to match
    cleaned_key = text.strip()
    if cleaned_key in LOCAL_TRANSLATIONS:
        translations = LOCAL_TRANSLATIONS[cleaned_key]
        if target_lang in translations:
            return translations[target_lang]

    # Try dynamic template translation first
    templated_msg = translate_templated_message(text, target_lang)
    if templated_msg:
        return templated_msg

    # Try dynamic support hours translation if it looks like support hours
    dynamic_hours = translate_hours_text(text, target_lang)
    if dynamic_hours:
        return dynamic_hours

    # Fallback to Gemini Translation
    key = os.getenv('GEMINI_API_KEY')
    if not key:
        return text

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
    headers = {
        'Content-Type': 'application/json'
    }

    lang_names = {
        'en': 'English',
        'hi': 'Hindi',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'ja': 'Japanese'
    }
    target_lang_name = lang_names.get(target_lang, 'English')

    prompt = (
        f"You are a professional translator. Translate the following text into {target_lang_name}. "
        "Keep the original format, including markdown like bold (**), newlines, and emojis. "
        "Return ONLY the translated text, with no extra explanation, intro, or quotes. "
        "Text to translate:\n"
        f"{text}"
    )

    body = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "maxOutputTokens": 1000,
            "temperature": 0.1
        }
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=10)
        if response.status_code == 200:
            data = response.json()
            translated = data['candidates'][0]['content']['parts'][0]['text'].strip()
            if (translated.startswith('"') and translated.endswith('"')) or (translated.startswith("'") and translated.endswith("'")):
                translated = translated[1:-1].strip()
            return translated
    except Exception as e:
        print(f"Translation to {target_lang} failed: {e}")
    return text
