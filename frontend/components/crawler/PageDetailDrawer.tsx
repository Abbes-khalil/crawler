import type { CrawledPage } from "@/types/crawler";
import { Drawer } from "@/components/ui/Drawer";

export function PageDetailDrawer({
  page,
  onClose,
}: {
  page: CrawledPage | null;
  onClose: () => void;
}) {
  return (
    <Drawer open={page !== null} onClose={onClose} title={page?.title ?? "Détails de la page"}>
      {page && (
        <div className="flex flex-col gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">URL</p>
            <a
              href={page.url}
              target="_blank"
              rel="noreferrer"
              className="break-all text-sm text-accent underline underline-offset-2"
            >
              {page.url}
            </a>
          </div>
          {page.meta_description && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                Méta-description
              </p>
              <p className="text-sm text-text">{page.meta_description}</p>
            </div>
          )}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                Statut
              </p>
              <p className="text-text">{page.status_code ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                Langue
              </p>
              <p className="text-text">{page.language ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                Méthode d&apos;analyse
              </p>
              <p className="text-text">{page.crawl_method}</p>
            </div>
          </div>
          <div>
            <p className="mb-1 text-xs font-medium uppercase tracking-wide text-text-muted">
              Contenu extrait
            </p>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-text">{page.text}</p>
          </div>
        </div>
      )}
    </Drawer>
  );
}
