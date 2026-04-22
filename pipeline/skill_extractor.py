import re

class SkillExtractor:
    def __init__(self):
        # A curated list of tech skills for B2B intelligence
        self.skill_db = {
            "Languages": ["python", "javascript", "typescript", "java", "golang", "rust", "c++", "c#", "ruby", "php", "swift", "kotlin"],
            "Cloud/Infra": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible", "jenkins"],
            "Frameworks": ["react", "next.js", "vue", "angular", "fastapi", "django", "flask", "spring boot", "node.js", "express"],
            "Data/ML": ["sql", "postgresql", "mongodb", "redis", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "spark", "hadoop", "tableau"],
            "Specialties": ["api", "microservices", "agile", "ci/cd", "rest", "graphql", "devops"]
        }
        # Flatten skills for easier matching
        self.all_skills = [skill for sublist in self.skill_db.values() for skill in sublist]

    def extract_skills(self, text):
        if not text:
            return []
        
        # Normalize text: lowercase and remove irregular symbols while keeping + # . -
        text = text.lower()
        text = re.sub(r'[^\w\s\+\#\-\.]', ' ', text)

        extracted = []
        for skill in self.all_skills:
            # Special regex handling for skills ending in non-word chars like C++, C#
            if skill.endswith('+') or skill.endswith('#'):
                pattern = rf'\b{re.escape(skill)}(?!\w)'
            else:
                pattern = rf'\b{re.escape(skill)}\b'
                
            if re.search(pattern, text):
                extracted.append(skill)
        
        return list(set(extracted))

if __name__ == "__main__":
    extractor = SkillExtractor()
    sample = "We are looking for a Python developer with experience in AWS and React. SQL is a plus."
    print(extractor.extract_skills(sample))
