"""Anatomy flashcard bank — each card has topic + diagram image."""
from __future__ import annotations

import re

from anatomy_photo_urls import TOPIC_PHOTO_URLS

TOPICS: tuple[str, ...] = (
    "Терминология и основы",
    "Опорно-двигательная",
    "Мышцы",
    "Сердечно-сосудистая",
    "Дыхательная",
    "Пищеварительная",
    "Мочевыделительная",
    "Нервная система",
    "Эндокринная",
    "Органы чувств",
    "Покровная система",
    "Лимфатическая",
    "Репродуктивная",
    "Головной мозг",
    "Позвоночник",
)

TOPIC_IMAGES: dict[str, list[str]] = TOPIC_PHOTO_URLS

# Local SVG fallbacks (offline mode: python3 generate_anatomy.py --local-svg)
TOPIC_SVG_IMAGES: dict[str, list[str]] = {
    "Терминология и основы": ["terminology-planes.svg", "terminology-directions.svg"],
    "Опорно-двигательная": ["skeleton-overview.svg", "bone-structure.svg", "joint-types.svg"],
    "Мышцы": ["muscle-structure.svg", "muscle-types.svg"],
    "Сердечно-сосудистая": ["heart.svg", "circulation.svg", "blood-vessels.svg"],
    "Дыхательная": ["lungs.svg", "respiratory-tract.svg"],
    "Пищеварительная": ["digestive.svg", "liver-gall.svg"],
    "Мочевыделительная": ["kidney.svg", "urinary.svg"],
    "Нервная система": ["neuron.svg", "cns-overview.svg"],
    "Эндокринная": ["endocrine.svg"],
    "Органы чувств": ["eye.svg", "ear.svg"],
    "Покровная система": ["skin.svg"],
    "Лимфатическая": ["lymphatic.svg"],
    "Репродуктивная": ["reproductive-m.svg", "reproductive-f.svg"],
    "Головной мозг": ["brain.svg", "brain-cortex.svg"],
    "Позвоночник": ["spine.svg", "spine-regions.svg"],
}

THEORY: dict[str, list[tuple[str, str]]] = {
    "Терминология и основы": [
        ("Что такое анатомия?", "Наука о форме и строении тела человека и животных; делится на макро- и микроскопическую."),
        ("Сагittal plane?", "Сагittalная плоскость делит тело на правую и левую части."),
        ("Frontal (coronal) plane?", "Фронтальная плоскость делит тело на переднюю и заднюю части."),
        ("Transverse plane?", "Поперечная (горизонтальная) плоскость делит тело на верхнюю и нижнюю части."),
        ("Что означает cranial / superior?", "К голове, выше (верхнее положение)."),
        ("Caudal / inferior?", "К хвосту/ногам, ниже."),
        ("Anterior / ventral?", "Передняя (ventral — животная сторона)."),
        ("Posterior / dorsal?", "Задняя (dorsal — спинная сторона)."),
        ("Medial vs lateral?", "Medial — ближе к срединной линии; lateral — дальше от неё."),
        ("Proximal vs distal?", "Proximal — ближе к туловищу; distal — дальше от туловища (для конечностей)."),
        ("Superficial vs deep?", "Поверхностный vs глубокий слой."),
        ("Что такое анатомическое положение?", "Стандартная поза: стоя, ладони вперёд, большие пальцы наружу."),
        ("Terms of movement: flexion?", "Сгибание — уменьшение угла в суставе."),
        ("Extension?", "Разгибание — увеличение угла в суставе."),
        ("Abduction / adduction?", "Отведение от срединной линии / приведение к ней."),
        ("Rotation?", "Вращение вокруг продольной оси кости или органа."),
        ("Что такое fascia?", "Соединительнотканная оболочка, окружающая мышцы и органы."),
        ("Сerosa / adventitia?", "Сerosa — у органов в полостях; adventitia — у органов вне полостей."),
        ("Что такое visceral vs parietal?", "Visceral — покрывает орган; parietal — выстилает стенку полости."),
        ("Homeostasis в контексте анатомии?", "Согласованная работа систем для стабильности внутренней среды."),
    ],
    "Опорно-двигательная": [
        ("Сколько костей у взрослого человека?", "Около 206 (вариабельно — сесамовидные, слияния)."),
        ("Диафиз и эпифиз?", "Диафиз — ствол кости; эпифиз — концевые части с суставными поверхностями."),
        ("Костный мозг?", "В полостях костей (красный — кроветворение, жёлтый — жир)."),
        ("Типы костей по форме?", "Длинные, короткие, плоские, нерегулярные, сесамовидные."),
        ("Синдесмоз / симфиз / синостоз?", "Сочленение соединительной тканью / хрящом / костью."),
        ("Synovial joint components?", "Суставная полость, синовиальная жидкость, суставной хрящ, кapsula."),
        ("Ball-and-socket joint пример?", "Плечевой и тазобедренный суставы."),
        ("Hinge joint пример?", "Локтевой, коленный."),
        ("Pivot joint?", "Атланто-аксиальный (C1–C2) — вращение головы."),
        ("Axial skeleton?", "Череп, позвоночник, грудная клетка."),
        ("Appendicular skeleton?", "Кости плечевого пояса, свободные конечности, таз."),
        ("Clavicle и scapula?", "Ключица и лопатка — пояс верхней конечности."),
        ("Pelvis?", "Подвздошные, седалищные, лобковые кости + крестец."),
        ("Fontanelles?", "«Мягкие точки» черепа новорождённого до окостенения."),
        ("Osteoblast / osteoclast?", "Клетки формирования / резорбции костной ткани."),
    ],
    "Мышцы": [
        ("Типы мышечной тissue?", "Поперечнополосатая (скелетная), гладкая, сердечная."),
        ("Origin vs insertion?", "Начало (проксимальнее, обычно неподвижнее) vs место прикрепления (движется)."),
        ("Agonist / antagonist?", "Мышца, выполняющая движение / противодействующая ему."),
        ("Synergist?", "Помогает agonist, стабилизирует сустав."),
        ("Fascicle arrangements?", "Параллельные, круговые, одноперистые, двуперистые, многоперистые."),
        ("Tendon?", "Плотное сухожилие — прикрепление мышцы к кости."),
        ("Aponeurosis?", "Широкое плоское сухожильное листовидное прикрепление."),
        ("Motor unit?", "Мотонейрон + все иннервируемые им мышечные волокна."),
        ("Что такое sarcomere?", "Функциональная единица поперечнополосатой мышцы между Z-линиями."),
        ("Actin и myosin?", "Белки, обеспечивающие скольжение и сокращение."),
        ("Isometric vs isotonic?", "Сокращение без изменения длины / с укорочением."),
        ("Slow-twitch vs fast-twitch fibers?", "Type I (выносливость) vs Type II (сила, скорость)."),
        ("Что такое motor end plate?", "Нервно-мышечное соединение — синапс на мышечном волокне."),
        ("Delayed onset muscle soreness?", "DOMS — микроповреждения после непривычной нагрузки."),
        ("Rotator cuff?", "Группа мышц стабилизирующих плечевой сустав (supraspinatus и др.)."),
    ],
    "Сердечно-сосудистая": [
        ("Камеры сердца?", "Правое и левое предсердия; правый и левый желудочки."),
        ("Клапаны сердца?", "Трicuspid, mitral (bicuspid), pulmonary, aortic."),
        ("Systole / diastole?", "Систола — сокращение; диастола — расслабление/наполнение."),
        ("Малый круг кровообращения?", "Правый желудочек → лёгочная артерия → лёгкие → лёгочные veins → левое предсердие."),
        ("Большой круг?", "Левый желудочек → аорта → органы → vena cava → правое предсердие."),
        ("Arteries vs veins?", "Артерии несут кровь от сердца (обычно богаты кислородом в большом круге); veins — к сердцу."),
        ("Что такое capillaries?", "Капилляры — обмен газов и питательных веществ с тканями."),
        ("Sinoatrial node?", "SA-узел — «пейсмeker» сердца в правом предсердии."),
        ("AV node и bundle of His?", "Проведение импульса предсердия → желудочки."),
        ("Coronary circulation?", "Коронарные артерии питают миокард."),
        ("Blood pressure systolic/diastolic?", "Давление при систоле / диастоле."),
        ("Что такое stroke volume?", "Объём крови, выбрасываемый желудочком за одно сокращение."),
        ("Atherosclerosis?", "Отложение бляшек в артериях — риск ишемии."),
        ("Lymph return role?", "Часть жидкости возвращается через лимфатическую систему в вены."),
        ("Portal circulation?", "Портальная система печени — вена из ЖКТ → печень → vena cava."),
    ],
    "Дыхательная": [
        ("Upper vs lower respiratory tract?", "Верхние: нос, глотка, гортань; нижние: трахея, бронхи, лёгкие."),
        ("Alveoli function?", "Газообмен: O₂ и CO₂ через alveolar-capillary membrane."),
        ("Diaphragm role?", "Главная мышца вдоха — опускается, увеличивая объём грудной полости."),
        ("External intercostals?", "Поднимают рёбра при вдохе."),
        ("Pleura?", "Visceral и parietal pleura с pleural cavity и fluid."),
        ("Conducting vs respiratory zone?", "Проведение воздуха без газообмена vs зона alveoli."),
        ("Surfactant?", "Снижает surface tension в alveoli — предотвращает collapse."),
        ("Vital capacity?", "Максимальный объём выдоха после максимального вдоха."),
        ("Anatomical dead space?", "Объём дыхательных путей без участия в газообмене."),
        ("Carina?", "Разветвление трахеи на главные bronchi."),
        ("Larynx и vocal cords?", "Гортань — голосовые связки, защита трахеи при глотании."),
        ("Epiglottis?", "Закрывает glottis при глотании."),
        ("Bronchi vs bronchioles?", "Проводящие пути с хрящом → без хряща, с smooth muscle."),
        ("Mediastinum?", "Средостение — сердце, крупные сосуды, трахея, пищевод."),
        ("Cough reflex anatomy?", "Раздражение receptors в airways → expiratory muscles."),
    ],
    "Пищеварительная": [
        ("Oral cavity role?", "Механическая обработка, salivary amylase, bolus formation."),
        ("Esophagus?", "Перistalsis доставляет пищу в stomach."),
        ("Stomach regions?", "Cardia, fundus, body, pylorus; gastric mucosa, glands."),
        ("Small intestine parts?", "Duodenum, jejunum, ileum — основное всасывание."),
        ("Large intestine?", "Cecum, colon, rectum — вода, electrolytes, microbiota."),
        ("Liver lobes?", "Печень — detox, bile production; left/right lobes, caudate, quadrate."),
        ("Gallbladder?", "Хранение и концентрация bile."),
        ("Pancreas exocrine/endocrine?", "Digestive enzymes (exocrine) + insulin/glucagon (islets of Langerhans)."),
        ("Villi и microvilli?", "Увеличивают surface area тонкой кишки."),
        ("Hepatic portal vein?", "Кровь из ЖКТ → печень перед systemic circulation."),
        ("Sphincter of Oddi?", "Кontrol bile/pancreatic juice entry в duodenum."),
        ("Appendix?", "Придаток cecum — lymphoid tissue."),
        ("Greater omentum?", "Жировая «фартук»-складка — защита и immmune role."),
        ("Mesentery?", "Прикрепление intestines к posterior abdominal wall."),
        ("Peristalsis mechanism?", "Coordinated smooth muscle contraction waves."),
    ],
    "Мочевыделительная": [
        ("Kidney structure?", "Cortex, medulla, renal pyramids, pelvis."),
        ("Nephron?", "Функциональная единица: glomerulus + tubules (PCT, loop of Henle, DCT)."),
        ("Glomerular filtration?", "Фильтрация plasma в Bowman's capsule."),
        ("Ureter, bladder, urethra?", "Проведение и хранение urine до выведения."),
        ("Detrusor muscle?", "Мышца стенки мочевого пузыря."),
        ("Internal vs external urethral sphincter?", "Involuntary smooth vs voluntary skeletal (perineum)."),
        ("Renal artery/vein?", "Кровоснабжение почки (~20% cardiac output)."),
        ("ADH effect on kidney?", "Увеличивает reabsorption воды в collecting ducts."),
        ("Aldosterone?", "Reabsorption Na⁺ в distal nephron."),
        ("Juxtaglomerular apparatus?", "Regulation renin release."),
        ("Micturition reflex?", "Bladder stretch → parasympathetic contraction; voluntary control external sphincter."),
        ("Renal calyces?", "Collect urine from pyramids into pelvis."),
        ("Countercurrent multiplier?", "Loop of Henle concentrates urine in medulla."),
        ("Prostate (male)?", "Surrounds urethra — secretions in semen."),
        ("Female urethra length?", "Короче — выше риск UTI."),
    ],
    "Нервная система": [
        ("CNS vs PNS?", "Central (brain, spinal cord) vs peripheral nerves, ganglia."),
        ("Neuron parts?", "Soma, dendrites, axon, synaptic terminals."),
        ("Myelin?", "Schwann cells (PNS) / oligodendrocytes (CNS) — saltatory conduction."),
        ("Synapse?", "Presynaptic neuron → synaptic cleft → postsynaptic neuron."),
        ("Grey vs white matter?", "Grey — cell bodies; white — myelinated tracts."),
        ("Spinal cord cross-section?", "Grey H-shape (horns), white columns, central canal."),
        ("Dorsal root vs ventral root?", "Sensory afferent vs motor efferent."),
        ("Reflex arc?", "Receptor → sensory neuron → interneuron → motor neuron → effector."),
        ("Autonomic sympathetic vs parasympathetic?", "Fight-or-flight vs rest-and-digest."),
        ("Cranial nerves count?", "12 пар (I–XII) — olfactory, optic, oculomotor, …)."),
        ("Blood-brain barrier?", "Tight junctions capillaries CNS — selective permeability."),
        ("CSF circulation?", "Choroid plexus → ventricles → subarachnoid space → absorption."),
        ("Meninges layers?", "Dura, arachnoid, pia mater."),
        ("Ganglion?", "Cluster of neuron cell bodies in PNS."),
        ("Tract vs nerve?", "CNS bundle of axons vs PNS bundle."),
    ],
    "Эндокринная": [
        ("Endocrine vs exocrine?", "Hormones в blood vs ducts наружу."),
        ("Hypothalamus-pituitary axis?", "Hypothalamus releasing hormones → anterior pituitary."),
        ("Thyroid hormones?", "T3/T4 — metabolism regulation; iodine needed."),
        ("Parathyroid?", "PTH — calcium homeostasis с костями и kidneys."),
        ("Adrenal cortex zones?", "Mineralocorticoids (aldosterone), glucocorticoids (cortisol), androgens."),
        ("Adrenal medulla?", "Epinephrine/norepinephrine — sympathetic response."),
        ("Pancreatic islets?", "Insulin (beta), glucagon (alpha)."),
        ("Pineal gland?", "Melatonin — circadian rhythm."),
        ("Negative feedback?", "Hormone уровень подавляет дальнейшую секрецию."),
        ("Target cell receptors?", "Cell-surface или intracellular (steroid hormones)."),
        ("Growth hormone source?", "Anterior pituitary — somatotrophs."),
        ("Oxytocin / ADH storage?", "Posterior pituitary releases hormones made in hypothalamus."),
        ("Thymus role?", "T-cell maturation ( prominent in children)."),
        ("Gonads endocrine?", "Testosterone / estrogen-progesterone."),
        ("Diabetes types anatomy link?", "Type 1 — beta cell destruction; type 2 — insulin resistance."),
    ],
    "Органы чувств": [
        ("Eye layers?", "Fibrous (sclera/cornea), vascular (choroid/ciliary/iris), retina."),
        ("Cornea vs lens?", "Cornea — фиксированная преломляющая поверхность; lens — accommodation."),
        ("Retina photoreceptors?", "Rods (dim light) vs cones (color, detail)."),
        ("Fovea centralis?", "Центральная ямка — максимальная acuity."),
        ("Optic nerve?", "CN II — axons ganglion cells → brain."),
        ("Ear outer/middle/inner?", "Pinna/ canal; ossicles; cochlea/vestibule."),
        ("Tympanic membrane?", "Eardrum — vibration to ossicles."),
        ("Cochlea function?", "Organ of Corti — hearing transduction."),
        ("Semicircular canals?", "Balance — rotational acceleration."),
        ("Taste buds location?", "Papillae tongue primarily; also soft palate, pharynx."),
        ("Olfactory epithelium?", "Upper nasal cavity — smell receptors."),
        ("Lacrimal apparatus?", "Tear production and drainage."),
        ("Extraocular muscles?", "Six muscles move each eye (CN III, IV, VI)."),
        ("Pupillary reflex?", "Light → CN II → midbrain → CN III constriction."),
        ("Presbyopia?", "Age-related lens stiffening — loss accommodation."),
    ],
    "Покровная система": [
        ("Skin layers?", "Epidermis, dermis, hypodermis (subcutaneous)."),
        ("Epidermis strata?", "Stratum corneum → basale (keratinocytes)."),
        ("Melanocytes?", "Melanin production — UV protection."),
        ("Dermis components?", "Collagen, elastin, blood vessels, nerves, appendages."),
        ("Hair follicle?", "Epithelial root sheath, dermal papilla, arrector pili."),
        ("Sebaceous glands?", "Sebum — lubrication skin/hair."),
        ("Eccrine vs apocrine sweat?", "Thermoregulation widespread vs body odor areas."),
        ("Nails structure?", "Nail plate, matrix, bed, lunula."),
        ("Pacinian corpuscles?", "Deep pressure/vibration mechanoreceptors in dermis."),
        ("Free nerve endings?", "Pain and temperature."),
        ("Barrier function?", "Prevents water loss and pathogen entry."),
        ("Vitamin D synthesis?", "UV in epidermis converts cholesterol derivatives."),
        ("Blister anatomy?", "Separation epidermis from dermis — fluid-filled."),
        ("Burn degrees?", "1st epidermis; 2nd partial dermis; 3rd full thickness."),
        ("Skin graft?", "Transplant epidermis/dermis for wound coverage."),
    ],
    "Лимфатическая": [
        ("Lymph composition?", "Interstitial fluid, lymphocytes, proteins returned to blood."),
        ("Lymph capillaries?", "Highly permeable — pick up excess tissue fluid."),
        ("Lymph nodes function?", "Filter lymph, immune activation (B/T cells)."),
        ("Major lymph node groups?", "Cervical, axillary, inguinal, mesenteric."),
        ("Thoracic duct?", "Largest lymph vessel — drains most body into left subclavian vein."),
        ("Right lymphatic duct?", "Drains right upper quadrant."),
        ("Spleen functions?", "Blood filtration, immune response, platelet storage."),
        ("Tonsils?", "Mucosa-associated lymphoid tissue — first defense pathogens."),
        ("Peyer's patches?", "Lymphoid follicles in ileum."),
        ("Lymphatic vs blood capillaries?", "One-way valves, no RBC, blind-ended."),
        ("Edema cause?", "Excess interstitial fluid when lymph/blood flow impaired."),
        ("Lymphedema?", "Chronic swelling from lymph obstruction."),
        ("Macrophages in nodes?", "Phagocytose pathogens and debris."),
        ("Adaptive immunity in nodes?", "Antigen presentation to lymphocytes."),
        ("Lymphatic role in fat absorption?", "Lacteals in villi transport chylomicrons."),
    ],
    "Репродуктивная": [
        ("Testes structure?", "Seminiferous tubules — spermatogenesis; interstitial Leydig cells — testosterone."),
        ("Epididymis / vas deferens?", "Sperm maturation and transport."),
        ("Prostate, seminal vesicles?", "Accessory glands — seminal fluid components."),
        ("Penis erectile tissue?", "Corpora cavernosa and spongiosum."),
        ("Ovaries?", "Oogenesis, estrogen/progesterone production."),
        ("Uterine tubes (fallopian)?", "Fertilization site; cilia move ovum."),
        ("Uterus layers?", "Endometrium, myometrium, perimetrium."),
        ("Menstrual cycle anatomy?", "Endometrial proliferation and shedding."),
        ("Placenta?", "Fetal-maternal exchange organ."),
        ("Breast (mammary) anatomy?", "Glandular lobules, ducts, adipose; lactiferous sinuses."),
        ("Puberty changes?", "Secondary sex characteristics via gonadal hormones."),
        ("Scrotum thermoregulation?", "Maintains optimal testicular temperature."),
        ("Cervix?", "Lower uterus — canal between uterus and vagina."),
        ("Broad ligament?", "Supports uterus and tubes in pelvis."),
        ("External genitalia homologues?", "Embryologic origin paired structures male/female."),
    ],
    "Головной мозг": [
        ("Brain major regions?", "Cerebrum, cerebellum, brainstem (midbrain, pons, medulla)."),
        ("Cerebral lobes?", "Frontal, parietal, temporal, occipital."),
        ("Primary motor cortex?", "Precentral gyrus — voluntary movement."),
        ("Somatosensory cortex?", "Postcentral gyrus — touch, pain, temperature."),
        ("Visual cortex?", "Occipital lobe — primary visual area."),
        ("Broca vs Wernicke areas?", "Speech production (frontal) vs comprehension (temporal)."),
        ("Basal ganglia?", "Caudate, putamen, globus pallidus — motor control."),
        ("Thalamus?", "Relay sensory/motor signals to cortex."),
        ("Hypothalamus functions?", "Homeostasis: temperature, hunger, hormones, circadian."),
        ("Hippocampus?", "Memory formation and spatial navigation."),
        ("Amygdala?", "Emotion processing, especially fear."),
        ("Corpus callosum?", "Commissural fibers connecting hemispheres."),
        ("Lateral ventricles?", "CSF-filled cavities in cerebrum."),
        ("Cerebellum function?", "Coordination, balance, motor learning."),
        ("Medulla vital centers?", "Breathing, heart rate, blood pressure reflexes."),
    ],
    "Позвоночник": [
        ("Vertebral regions?", "Cervical (7), thoracic (12), lumbar (5), sacral (5 fused), coccyx."),
        ("Typical vertebra parts?", "Body, vertebral arch, spinous process, transverse processes, foramen."),
        ("Intervertebral disc?", "Nucleus pulposus (gel) + annulus fibrosus (fibrocartilage)."),
        ("C1 (atlas) / C2 (axis)?", "Atlas supports skull; axis has dens for rotation."),
        ("Spinal curvatures?", "Cervical/lumbar lordosis; thoracic/sacral kyphosis."),
        ("Ligamentum flavum?", "Elastic ligament between laminae — aids extension."),
        ("Spinal nerves count?", "31 pairs — exit via intervertebral foramina."),
        ("Cauda equina?", "Lumbar/sacral nerve roots below L2 in subarachnoid space."),
        ("Epidural space?", "Fat and veins outside dura — site epidural anesthesia."),
        ("Herniated disc?", "Nucleus protrudes through annulus — may compress nerve root."),
        ("Scoliosis?", "Lateral curvature spine."),
        ("Spinous process palpation?", "Landmarks C7, T3/T7, L4 (iliac crest level)."),
        ("Facet joints?", "Zygapophyseal — guide motion between vertebrae."),
        ("Vertebral canal?", "Houses spinal cord (upper) and cauda equina (lower)."),
        ("Whiplash injury?", "Hyperextension/flexion cervical spine — soft tissue trauma."),
    ],
}

REVISION_HINTS: dict[str, list[str]] = {
    "Терминология и основы": ["плоскости", "направления", "движения", "положение тела"],
    "Опорно-двигательная": ["кости", "суставы", "череп", "таз"],
    "Мышцы": ["сокращение", "прикрепление", "типы волокон", "сухожилия"],
    "Сердечно-сосудистая": ["сердце", "клапаны", "круги кровообращения", "сосуды"],
    "Дыхательная": ["лёгкие", "альвеолы", "диафрагма", "бронхи"],
    "Пищеварительная": ["ЖКТ", "печень", "поджелудочная", "всасывание"],
    "Мочевыделительная": ["нефрон", "почка", "мочевой пузырь", "фильтрация"],
    "Нервная система": ["нейрон", "синапс", "спинной мозг", "ЧМН"],
    "Эндокринная": ["гормоны", "гипофиз", "щитовидная", "надпочечники"],
    "Органы чувств": ["глаз", "ухо", "сетчатка", "равновесие"],
    "Покровная система": ["кожа", "эпидермис", "волосы", "рецепторы"],
    "Лимфатическая": ["лимфа", "узлы", "селезёнка", "тимус"],
    "Репродуктивная": ["яичники", "матка", "яички", "плацента"],
    "Головной мозг": ["кора", "доли", "мозжечок", "таламус"],
    "Позвоночник": ["диск", "шейный отдел", "поясничный", "корешки"],
}


def _image_for(topic: str, index: int) -> str:
    images = TOPIC_IMAGES[topic]
    item = images[index % len(images)]
    if item.startswith("http://") or item.startswith("https://"):
        return item
    return f"anatomy-assets/{item}"


def _alt_for(topic: str, index: int) -> str:
    images = TOPIC_IMAGES[topic]
    item = images[index % len(images)]
    if item.startswith("http://") or item.startswith("https://"):
        name = item.rstrip("/").split("/")[-1]
        name = re.sub(r"^\d+px-", "", name.split("?", 1)[0])
        name = name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
    else:
        name = item.replace(".svg", "").replace("-", " ")
    return f"{topic}: {name}"


def use_local_svg_images() -> None:
    """Switch to bundled SVG diagrams (offline)."""
    global TOPIC_IMAGES
    TOPIC_IMAGES = TOPIC_SVG_IMAGES


def anatomy_card(question: str, reference: str, topic: str, image_index: int = 0) -> dict:
    return {
        "card_type": "anatomy",
        "question": question,
        "reference": reference,
        "topic": topic,
        "image": _image_for(topic, image_index),
        "image_alt": _alt_for(topic, image_index),
    }


def build_cards() -> list[dict]:
    cards: list[dict] = []
    idx = 0
    for topic, pairs in THEORY.items():
        for i, (q, ref) in enumerate(pairs):
            cards.append(anatomy_card(q, ref, topic, image_index=i))
            idx += 1

    for topic, hints in REVISION_HINTS.items():
        for hint in hints:
            for n in range(5):
                cards.append(
                    anatomy_card(
                        f"Анатомия [{topic}]: {hint} — вопрос #{n + 1}",
                        f"Дай развёрнутый ответ по теме «{hint}» в разделе {topic}. "
                        f"Укажи ключевые структуры, функции и взаимосвязи.",
                        topic,
                        image_index=n + len(hints),
                    )
                )

    seen: set[str] = set()
    unique: list[dict] = []
    for card in cards:
        key = card["question"]
        if key in seen:
            continue
        seen.add(key)
        if not card.get("image"):
            raise ValueError(f"Card without image: {card['question'][:60]}")
        unique.append(card)
    return unique
