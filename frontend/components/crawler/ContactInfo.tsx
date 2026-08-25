import type { Observation } from "@/types/crawler";
import { Card } from "@/components/ui/Card";

const SOCIAL_FIELDS = [
  "linkedin_url",
  "facebook_url",
  "instagram_url",
  "youtube_url",
  "twitter_url",
];

function uniqueValues(observations: Observation[], field: string): Observation[] {
  const seen = new Set<string>();
  const result: Observation[] = [];

  for (const obs of observations) {
    if (obs.field !== field) continue;
    const key = obs.normalized_value ?? obs.raw_value;
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(obs);
  }

  return result;
}

function ValueList({ values }: { values: Observation[] }) {
  return (
    <ul className="flex flex-col gap-1">
      {values.map((obs) => (
        <li key={`${obs.field}-${obs.raw_value}`}>
          <a
            href={obs.source_url}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-text underline decoration-border underline-offset-2 hover:text-accent"
          >
            {obs.normalized_value ?? obs.raw_value}
          </a>
        </li>
      ))}
    </ul>
  );
}

export function ContactInfo({ observations }: { observations: Observation[] }) {
  const emails = uniqueValues(observations, "email");
  const phones = uniqueValues(observations, "phone");
  const organizationNames = uniqueValues(observations, "organization_name");
  const socials = observations.filter((obs) => SOCIAL_FIELDS.includes(obs.field));

  return (
    <Card>
      <h2 className="mb-3 text-sm font-semibold text-text">Contact information</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-text-muted">Email</p>
          {emails.length > 0 ? (
            <ValueList values={emails} />
          ) : (
            <p className="text-sm text-text-muted">Not found</p>
          )}
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-text-muted">Phone</p>
          {phones.length > 0 ? (
            <ValueList values={phones} />
          ) : (
            <p className="text-sm text-text-muted">Not found</p>
          )}
        </div>
        {organizationNames.length > 0 && (
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
              Organization
            </p>
            <ValueList values={organizationNames} />
          </div>
        )}
        {socials.length > 0 && (
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">Social</p>
            <ValueList values={socials} />
          </div>
        )}
      </div>
    </Card>
  );
}
