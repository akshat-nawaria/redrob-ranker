import sys, json
sys.stdout.reconfigure(encoding='utf-8')

DATA = r'c:\Users\Akshyat\Downloads\[PUB] India_runs_data_and_ai_challenge\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl'

count = 0
titles = {}
industries = {}
countries = {}
exp_buckets = {"0-2": 0, "2-5": 0, "5-9": 0, "9-15": 0, "15+": 0}
skill_counts = {}

with open(DATA, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        c = json.loads(line)
        count += 1
        
        t = c['profile']['current_title']
        titles[t] = titles.get(t, 0) + 1
        
        i = c['profile']['current_industry']
        industries[i] = industries.get(i, 0) + 1
        
        co = c['profile']['country']
        countries[co] = countries.get(co, 0) + 1
        
        yoe = c['profile']['years_of_experience']
        if yoe < 2: exp_buckets["0-2"] += 1
        elif yoe < 5: exp_buckets["2-5"] += 1
        elif yoe < 9: exp_buckets["5-9"] += 1
        elif yoe < 15: exp_buckets["9-15"] += 1
        else: exp_buckets["15+"] += 1
        
        for sk in c.get('skills', []):
            name = sk['name']
            skill_counts[name] = skill_counts.get(name, 0) + 1

print(f"Total candidates: {count}")
print(f"\nTop 25 Titles:")
for k, v in sorted(titles.items(), key=lambda x: -x[1])[:25]:
    print(f"  {k}: {v}")

print(f"\nIndustries:")
for k, v in sorted(industries.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

print(f"\nCountries:")
for k, v in sorted(countries.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

print(f"\nExperience distribution:")
for k, v in exp_buckets.items():
    print(f"  {k} years: {v}")

print(f"\nTop 40 Skills:")
for k, v in sorted(skill_counts.items(), key=lambda x: -x[1])[:40]:
    print(f"  {k}: {v}")
