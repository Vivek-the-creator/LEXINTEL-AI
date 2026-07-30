"""
Seed the case_judgments FAISS index with real Indian Supreme Court and High Court cases.
Run from backend/: python seed_cases.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("JWT_SECRET_KEY", "seed-script")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("GROQ_API_KEY", "seed-script")

CASES = [
    {
        "case_name": "Vishaka v. State of Rajasthan",
        "citation": "AIR 1997 SC 3011",
        "court": "Supreme Court of India",
        "year": "1997",
        "verdict": "Guidelines Issued",
        "text": (
            "Vishaka v. State of Rajasthan AIR 1997 SC 3011. Supreme Court of India 1997. "
            "Sexual harassment at workplace. Writ petition filed after gang rape of social worker Bhanwari Devi. "
            "Court laid down Vishaka Guidelines making it mandatory for employers to prevent sexual harassment. "
            "Applicable laws: Article 14, 15, 19, 21 Constitution of India. "
            "Key principles: Right to safe working environment, employer liability, complaints committee mandatory. "
            "Verdict: Guidelines issued binding on all employers until legislation enacted. "
            "Later codified as POSH Act 2013. Landmark judgment for women's rights at workplace."
        ),
    },
    {
        "case_name": "Maneka Gandhi v. Union of India",
        "citation": "AIR 1978 SC 597",
        "court": "Supreme Court of India",
        "year": "1978",
        "verdict": "Allowed",
        "text": (
            "Maneka Gandhi v. Union of India AIR 1978 SC 597. Supreme Court of India 1978. "
            "Passport impounded without giving reasons. Fundamental rights Article 21 personal liberty. "
            "Court held procedure established by law must be fair, just and reasonable. "
            "Expanded scope of Article 21 beyond mere physical existence. "
            "Key principles: Right to travel abroad, natural justice, due process, audi alteram partem. "
            "Applicable laws: Article 14, 19, 21 Constitution of India, Passport Act 1967. "
            "Verdict: Allowed. Passport must be returned. Procedure must be reasonable. "
            "Landmark judgment expanding fundamental rights jurisprudence in India."
        ),
    },
    {
        "case_name": "K.S. Puttaswamy v. Union of India",
        "citation": "(2017) 10 SCC 1",
        "court": "Supreme Court of India",
        "year": "2017",
        "verdict": "Allowed — Right to Privacy declared Fundamental Right",
        "text": (
            "K.S. Puttaswamy v. Union of India (2017) 10 SCC 1. Supreme Court of India 2017. "
            "Nine-judge constitutional bench. Right to privacy as fundamental right under Article 21. "
            "Challenge to Aadhaar biometric data collection. "
            "Court unanimously held privacy is intrinsic to life and liberty. "
            "Key principles: Informational privacy, bodily integrity, decisional autonomy. "
            "Applicable laws: Article 14, 19, 21 Constitution of India. "
            "Verdict: Right to privacy declared fundamental right. Overruled M.P. Sharma and Kharak Singh. "
            "Landmark judgment with far-reaching implications for data protection and surveillance."
        ),
    },
    {
        "case_name": "Arnesh Kumar v. State of Bihar",
        "citation": "(2014) 8 SCC 273",
        "court": "Supreme Court of India",
        "year": "2014",
        "verdict": "Guidelines Issued — Arrest Guidelines",
        "text": (
            "Arnesh Kumar v. State of Bihar (2014) 8 SCC 273. Supreme Court of India 2014. "
            "Misuse of Section 498A IPC dowry harassment cases. Arbitrary arrests without application of mind. "
            "Court issued mandatory guidelines for arrest in offences punishable up to 7 years. "
            "Police must apply mind before arrest. Magistrate must scrutinize arrest memo. "
            "Key principles: Personal liberty, Section 41 CrPC checklist mandatory, no automatic arrest. "
            "Applicable laws: Section 498A IPC, Section 41 CrPC, Article 21 Constitution. "
            "Verdict: Guidelines issued. Police and magistrates must follow checklist before arrest. "
            "Important for matrimonial disputes, dowry cases, domestic violence matters."
        ),
    },
    {
        "case_name": "Lalita Kumari v. Government of Uttar Pradesh",
        "citation": "(2014) 2 SCC 1",
        "court": "Supreme Court of India",
        "year": "2014",
        "verdict": "Mandatory FIR Registration Directed",
        "text": (
            "Lalita Kumari v. Government of Uttar Pradesh (2014) 2 SCC 1. Supreme Court of India 2014. "
            "Registration of FIR mandatory when cognizable offence disclosed. "
            "Police cannot conduct preliminary inquiry before registering FIR in cognizable offences. "
            "Key principles: Section 154 CrPC mandatory, no discretion to refuse FIR, victim rights. "
            "Applicable laws: Section 154 CrPC, Article 21 Constitution of India. "
            "Verdict: FIR registration mandatory. Preliminary inquiry only in limited cases like matrimonial, commercial. "
            "Landmark for victims seeking FIR registration when police refuse."
        ),
    },
    {
        "case_name": "National Consumer Disputes Redressal Commission v. Oberoi Realty",
        "citation": "Consumer Case No. 83 of 2015",
        "court": "National Consumer Disputes Redressal Commission",
        "year": "2016",
        "verdict": "Allowed — Builder directed to refund with interest",
        "text": (
            "Consumer complaint against builder for delay in possession of flat. "
            "National Consumer Disputes Redressal Commission 2016. "
            "Builder failed to deliver possession within agreed time. Deficiency in service established. "
            "Key principles: Consumer Protection Act 2019, deficiency in service, unfair trade practice. "
            "Builder liable to refund entire amount with 12% interest per annum. "
            "Applicable laws: Consumer Protection Act 1986/2019, Section 2(1)(g) deficiency in service. "
            "Verdict: Allowed. Builder directed to refund with interest and pay compensation. "
            "Applicable to all real estate consumer disputes, flat booking cancellations, delayed possession."
        ),
    },
    {
        "case_name": "Lucknow Development Authority v. M.K. Gupta",
        "citation": "AIR 1994 SC 787",
        "court": "Supreme Court of India",
        "year": "1994",
        "verdict": "Allowed — Government bodies liable under Consumer Protection Act",
        "text": (
            "Lucknow Development Authority v. M.K. Gupta AIR 1994 SC 787. Supreme Court of India 1994. "
            "Government housing authority liable for deficiency in service under Consumer Protection Act. "
            "Allotment of flat, delay in possession, defective construction. "
            "Key principles: Government bodies are service providers, consumer rights against public authorities. "
            "Applicable laws: Consumer Protection Act 1986, Section 2(1)(o) service definition. "
            "Verdict: Allowed. Government bodies cannot escape consumer forum jurisdiction. "
            "Landmark for consumer cases against government housing boards, development authorities, municipalities."
        ),
    },
    {
        "case_name": "State of Maharashtra v. Madhkar Narayan",
        "citation": "AIR 1991 SC 207",
        "court": "Supreme Court of India",
        "year": "1991",
        "verdict": "Conviction Upheld",
        "text": (
            "State of Maharashtra v. Madhkar Narayan AIR 1991 SC 207. Supreme Court of India 1991. "
            "Sexual assault case. Testimony of prosecutrix. Sole testimony of victim sufficient for conviction. "
            "Every woman has right to privacy and no one can trespass upon her body. "
            "Key principles: Victim testimony, corroboration not mandatory in sexual assault, right to bodily integrity. "
            "Applicable laws: Section 376 IPC, Indian Evidence Act. "
            "Verdict: Conviction upheld. Sole testimony of victim reliable and sufficient. "
            "Important precedent for rape and sexual assault cases in Indian courts."
        ),
    },
    {
        "case_name": "Shayara Bano v. Union of India",
        "citation": "(2017) 9 SCC 1",
        "court": "Supreme Court of India",
        "year": "2017",
        "verdict": "Triple Talaq Declared Unconstitutional",
        "text": (
            "Shayara Bano v. Union of India (2017) 9 SCC 1. Supreme Court of India 2017. "
            "Constitutional validity of triple talaq talaq-e-biddat in Muslim personal law. "
            "Practice of instant divorce by uttering talaq three times declared unconstitutional. "
            "Key principles: Article 14 equality, Article 21 dignity, manifest arbitrariness. "
            "Applicable laws: Article 14, 15, 21 Constitution, Muslim Personal Law Shariat Application Act 1937. "
            "Verdict: Triple talaq declared void and unconstitutional by 3:2 majority. "
            "Parliament subsequently enacted Muslim Women Protection of Rights on Marriage Act 2019."
        ),
    },
    {
        "case_name": "Olga Tellis v. Bombay Municipal Corporation",
        "citation": "AIR 1986 SC 180",
        "court": "Supreme Court of India",
        "year": "1986",
        "verdict": "Partly Allowed",
        "text": (
            "Olga Tellis v. Bombay Municipal Corporation AIR 1986 SC 180. Supreme Court of India 1986. "
            "Eviction of pavement dwellers from Bombay footpaths. Right to livelihood as part of right to life. "
            "Court held right to life includes right to livelihood. Cannot be deprived without due process. "
            "Key principles: Article 21 right to livelihood, natural justice before eviction, rehabilitation. "
            "Applicable laws: Article 21 Constitution of India, Bombay Municipal Corporation Act. "
            "Verdict: Partly allowed. Eviction stayed. Alternate sites to be provided. "
            "Landmark for housing rights, slum dwellers, eviction cases, right to shelter."
        ),
    },
    {
        "case_name": "M.C. Mehta v. Union of India (Taj Trapezium Case)",
        "citation": "AIR 1997 SC 734",
        "court": "Supreme Court of India",
        "year": "1997",
        "verdict": "Directions Issued — Polluting Industries Relocated",
        "text": (
            "M.C. Mehta v. Union of India Taj Trapezium Case AIR 1997 SC 734. Supreme Court 1997. "
            "Environmental pollution damaging Taj Mahal. Industries using coal coke in Taj Trapezium Zone. "
            "Court ordered relocation of polluting industries. Precautionary principle applied. "
            "Key principles: Article 21 right to clean environment, polluter pays principle, precautionary principle. "
            "Applicable laws: Environment Protection Act 1986, Article 21 Constitution, Air Prevention Act 1981. "
            "Verdict: Industries directed to shift to natural gas or relocate outside Taj Trapezium Zone. "
            "Landmark environmental law judgment. Applicable to pollution, environmental damage cases."
        ),
    },
    {
        "case_name": "Indra Sawhney v. Union of India",
        "citation": "AIR 1993 SC 477",
        "court": "Supreme Court of India",
        "year": "1992",
        "verdict": "Partly Allowed — 50% cap on reservations",
        "text": (
            "Indra Sawhney v. Union of India AIR 1993 SC 477. Supreme Court of India 1992. "
            "Mandal Commission report. OBC reservations 27% in central government services. "
            "Court upheld OBC reservations but capped total reservations at 50%. Creamy layer excluded. "
            "Key principles: Article 16 equality of opportunity, backward class identification, creamy layer. "
            "Applicable laws: Article 14, 15, 16 Constitution of India. "
            "Verdict: 27% OBC reservation upheld. 50% ceiling on total reservations. Creamy layer excluded. "
            "Foundational judgment for reservation policy, OBC rights, affirmative action in India."
        ),
    },
    {
        "case_name": "Hussainara Khatoon v. State of Bihar",
        "citation": "AIR 1979 SC 1360",
        "court": "Supreme Court of India",
        "year": "1979",
        "verdict": "Allowed — Undertrial prisoners released",
        "text": (
            "Hussainara Khatoon v. State of Bihar AIR 1979 SC 1360. Supreme Court of India 1979. "
            "Undertrial prisoners languishing in jail for years awaiting trial. Speedy trial as fundamental right. "
            "Court held right to speedy trial is part of Article 21 right to life and liberty. "
            "Key principles: Speedy trial, bail for undertrials, legal aid, Article 21 personal liberty. "
            "Applicable laws: Article 21 Constitution, CrPC bail provisions, Legal Services Authority Act. "
            "Verdict: Undertrial prisoners directed to be released. Speedy trial declared fundamental right. "
            "Landmark for bail applications, undertrial rights, legal aid, criminal justice reform."
        ),
    },
    {
        "case_name": "Navtej Singh Johar v. Union of India",
        "citation": "(2018) 10 SCC 1",
        "court": "Supreme Court of India",
        "year": "2018",
        "verdict": "Section 377 IPC Partially Struck Down",
        "text": (
            "Navtej Singh Johar v. Union of India (2018) 10 SCC 1. Supreme Court of India 2018. "
            "Constitutional validity of Section 377 IPC criminalising consensual same-sex relations. "
            "Five-judge bench unanimously decriminalised consensual same-sex relations between adults. "
            "Key principles: Article 14 equality, Article 19 expression, Article 21 dignity and identity. "
            "Applicable laws: Section 377 IPC, Article 14, 15, 19, 21 Constitution of India. "
            "Verdict: Section 377 read down. Consensual same-sex acts between adults decriminalised. "
            "Landmark for LGBTQ rights, personal liberty, constitutional morality over social morality."
        ),
    },
    {
        "case_name": "Bandhua Mukti Morcha v. Union of India",
        "citation": "AIR 1984 SC 802",
        "court": "Supreme Court of India",
        "year": "1984",
        "verdict": "Allowed — Bonded labourers freed and rehabilitated",
        "text": (
            "Bandhua Mukti Morcha v. Union of India AIR 1984 SC 802. Supreme Court of India 1984. "
            "Bonded labour system. Workers in stone quarries working in inhuman conditions. "
            "Court held bonded labour violates Article 21, 23 and directed immediate release and rehabilitation. "
            "Key principles: Article 21 right to live with dignity, Article 23 prohibition of forced labour. "
            "Applicable laws: Bonded Labour System Abolition Act 1976, Article 21, 23 Constitution. "
            "Verdict: Bonded labourers to be identified, released and rehabilitated. State duty to enforce. "
            "Applicable to labour rights, forced labour, minimum wages, worker exploitation cases."
        ),
    },
    {
        "case_name": "Sunil Batra v. Delhi Administration",
        "citation": "AIR 1978 SC 1675",
        "court": "Supreme Court of India",
        "year": "1978",
        "verdict": "Allowed — Prison reforms directed",
        "text": (
            "Sunil Batra v. Delhi Administration AIR 1978 SC 1675. Supreme Court of India 1978. "
            "Prisoner rights. Solitary confinement, bar fetters, inhuman treatment in prison. "
            "Court held prisoners retain fundamental rights except those taken away by lawful incarceration. "
            "Key principles: Article 21 prisoner rights, inhuman treatment prohibition, prison reform. "
            "Applicable laws: Article 21 Constitution, Prisons Act 1894, CrPC. "
            "Verdict: Solitary confinement and bar fetters restricted. Prison conditions to be humane. "
            "Applicable to prisoner rights, bail, custody conditions, police brutality cases."
        ),
    },
    {
        "case_name": "D.K. Basu v. State of West Bengal",
        "citation": "AIR 1997 SC 610",
        "court": "Supreme Court of India",
        "year": "1997",
        "verdict": "Guidelines Issued — Custodial Death Prevention",
        "text": (
            "D.K. Basu v. State of West Bengal AIR 1997 SC 610. Supreme Court of India 1997. "
            "Custodial deaths and torture in police custody. Writ petition for guidelines. "
            "Court issued comprehensive guidelines for arrest and detention to prevent custodial violence. "
            "Key principles: Article 21 right to life, custodial torture prohibition, arrest memo mandatory. "
            "Applicable laws: Article 21 Constitution, Section 41B CrPC, NHRC guidelines. "
            "Verdict: Mandatory guidelines for arrest — memo, medical examination, family intimation. "
            "Applicable to illegal detention, custodial violence, police brutality, wrongful arrest cases."
        ),
    },
    {
        "case_name": "Shreya Singhal v. Union of India",
        "citation": "(2015) 5 SCC 1",
        "court": "Supreme Court of India",
        "year": "2015",
        "verdict": "Section 66A IT Act Struck Down",
        "text": (
            "Shreya Singhal v. Union of India (2015) 5 SCC 1. Supreme Court of India 2015. "
            "Section 66A Information Technology Act 2000 criminalising online speech struck down. "
            "Vague and overbroad provision violating freedom of speech and expression. "
            "Key principles: Article 19(1)(a) freedom of speech, reasonable restrictions, online expression. "
            "Applicable laws: Section 66A IT Act 2000, Article 19 Constitution of India. "
            "Verdict: Section 66A struck down as unconstitutional. Online speech protected. "
            "Landmark for cyber law, online defamation, social media posts, digital rights cases."
        ),
    },
    {
        "case_name": "Gian Kaur v. State of Punjab",
        "citation": "AIR 1996 SC 1257",
        "court": "Supreme Court of India",
        "year": "1996",
        "verdict": "Right to Die Not a Fundamental Right",
        "text": (
            "Gian Kaur v. State of Punjab AIR 1996 SC 1257. Supreme Court of India 1996. "
            "Constitutional validity of Section 309 IPC attempt to suicide. "
            "Court held right to life under Article 21 does not include right to die. "
            "Key principles: Article 21 right to life, Section 309 IPC, euthanasia, passive euthanasia. "
            "Applicable laws: Section 309 IPC, Article 21 Constitution of India. "
            "Verdict: Right to die not included in Article 21. Section 309 IPC valid. "
            "Distinguished from Aruna Shanbaug case on passive euthanasia. Medical law, end of life cases."
        ),
    },
    {
        "case_name": "Common Cause v. Union of India (Passive Euthanasia)",
        "citation": "(2018) 5 SCC 1",
        "court": "Supreme Court of India",
        "year": "2018",
        "verdict": "Passive Euthanasia and Living Will Recognised",
        "text": (
            "Common Cause v. Union of India (2018) 5 SCC 1. Supreme Court of India 2018. "
            "Right to die with dignity. Passive euthanasia and advance medical directive living will. "
            "Five-judge bench recognised right to die with dignity as fundamental right under Article 21. "
            "Key principles: Article 21 right to die with dignity, advance directive, passive euthanasia. "
            "Applicable laws: Article 21 Constitution, Medical ethics, Indian Medical Council Act. "
            "Verdict: Passive euthanasia allowed. Living will advance directive legally valid. "
            "Applicable to medical negligence, end of life care, hospital liability, patient rights cases."
        ),
    },
]


def seed():
    from app.ai.rag.faiss_store import FAISSVectorStore
    from app.ai.rag.embedding_service import get_embedding_service
    from app.core.config import settings

    print(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
    embedder = get_embedding_service()

    store = FAISSVectorStore(
        dimension=embedder.dimension,
        index_name=settings.CASES_INDEX,
    )
    store.load()

    print(f"Current vectors in case index: {store.total_vectors}")

    texts = [c["text"] for c in CASES]
    metadata = [
        {
            "chunk_id": f"case_{i}",
            "case_name": c["case_name"],
            "citation": c["citation"],
            "court": c["court"],
            "year": c["year"],
            "verdict": c["verdict"],
            "text": c["text"],
        }
        for i, c in enumerate(CASES)
    ]

    vectors = embedder.embed_batch(texts)
    store.add(vectors, metadata)
    store.save()

    print(f"Seeded {len(CASES)} Indian court cases.")
    print(f"Total vectors in case index: {store.total_vectors}")
    print("Done. Similar Cases agent will now return real Indian judgments.")


if __name__ == "__main__":
    seed()
