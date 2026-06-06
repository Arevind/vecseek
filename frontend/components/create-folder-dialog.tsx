"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { createFolder } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/toast-provider";

const FUNNY_FOLDER_PLACEHOLDERS = [
  "CEO Panic Button Docs",
  "Definitely Final Final Files",
  "Spreadsheet of Mild Regret",
  "The Folder Formerly Known as Urgent",
  "Chaos But Organized",
  "Not Suspicious Receipts",
  "Meeting Notes Nobody Asked For",
  "The Good PDF Pile",
  "Oops All SOPs",
  "Mission Control for Mayhem",
  "Paperwork and Vibes",
  "The Great Attachment Archive",
  "Unreasonably Important Text Files",
  "Snacks Budget Intelligence",
  "Invoice Avengers",
  "PDFs Against Humanity",
  "Operation Find The Latest Version",
  "The Vault of Tiny Headaches",
  "Legal-ish But Friendly",
  "Highly Decorated Documents",
  "Customer Drama Anthology",
  "Folder McFolderface",
  "Ctrl Alt Elite",
  "Receipts of Destiny",
  "The Compliance Casserole",
  "Oops We Indexed It Again",
  "Tiny Files Big Feelings",
  "The Department of Neat Chaos",
  "Audit Gremlin Evidence",
  "Excel and Exhale",
  "PowerPoint Witness Protection",
  "What Even Is Version 9",
  "The Official Misc Misc Folder",
  "Chronicles of Mild Panic",
  "This One Is Actually Final",
  "Do Not Yeet These Docs",
  "PDF Petting Zoo",
  "Slightly Fancy Paper Trail",
  "The Folder of Last Resorts",
  "Tax Season Survival Kit",
  "Oops Our Docs Are Showing",
  "Neatly Sorted Shenanigans",
  "Executive Snack Protocol",
  "The Big Book of Small Issues",
  "Memoirs of a Lost Attachment",
  "Client Questions We Pretend Were Easy",
  "Midnight Compliance Club",
  "Where The Good Answers Live",
  "The Archive Strikes Back",
  "Quarterly Confusion Capsule",
  "Oopsie Knowledge Drop",
  "The Search Bar Buffet",
  "Cashflow and Carry On",
  "The SOP Speakeasy",
  "Boardroom Breadcrumbs",
  "Helpdesk Greatest Hits",
  "This Folder Pays Rent",
  "Notion Escape Pod",
  "Clipboard Cinematic Universe",
  "The Neat Freak Bunker",
  "Whispers of Procurement",
  "One Folder To Rule Them All",
  "The Accidental Masterpiece",
  "Customer Chaos Cookbook",
  "Professional Looking Mess",
  "The Nice Clean Evidence Pile",
  "Finance Goblin Treasury",
  "Please Let This Be Searchable",
  "Business Secrets But Polite",
  "Coffee Powered Archives",
  "The Folder of Fancy Truths",
  "Oops All Knowledge",
  "Memos and Miracles",
  "Can Somebody Read This PDF",
  "The Big Little Document Club",
  "Internal Drama Starter Pack",
  "Files We Swear Are Useful",
  "The Department of Tiny Triumphs",
  "Borrowed Time Records",
  "Questions From The Void",
  "Premium Miscellaneous",
  "This Could Have Been An Email",
  "Operational Sparkle Drawer",
  "The Last Good Attachment",
  "SOP Safari",
  "Respectfully Unhinged Docs",
  "Search Me Maybe",
  "Where Did We Put That Thing",
  "Tenderly Curated Chaos",
  "The Great PDF Bakeoff",
  "Mildly Heroic Records",
  "Please Clap For This Folder",
  "Glossary of Confusion",
  "File Me Maybe",
  "KPI Karaoke Lyrics",
  "The Calm Before The Audit",
  "This Folder Has Main Character Energy",
  "Very Important Probably",
  "The Attachment Appreciation Society",
  "Inbox Archaeology Unit",
  "The Folder With The Good Biscuits",
  "Escalations and Espresso",
  "The Ministry of Useful Things",
];

function getRandomPlaceholder() {
  const index = Math.floor(Math.random() * FUNNY_FOLDER_PLACEHOLDERS.length);
  return FUNNY_FOLDER_PLACEHOLDERS[index];
}

export function CreateFolderDialog() {
  const queryClient = useQueryClient();
  const { pushToast } = useToast();
  const [open, setOpen] = useState(false);
  const [folderName, setFolderName] = useState("");
  const [error, setError] = useState("");
  const [placeholder, setPlaceholder] = useState(getRandomPlaceholder);

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);

    if (nextOpen) {
      setError("");
      setPlaceholder(getRandomPlaceholder());
    }
  };

  const mutation = useMutation({
    mutationFn: createFolder,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["folders"] });
      setFolderName("");
      setError("");
      setOpen(false);
      setPlaceholder(getRandomPlaceholder());
      pushToast({ tone: "success", title: "Folder created", description: "The new dock is ready for uploads." });
    },
    onError: (err: unknown) => {
      const message = getApiErrorMessage(err);
      setError(message);
      pushToast({ tone: "error", title: "Folder creation failed", description: message });
    },
  });

  return (
    <Dialog
      open={open}
      onOpenChange={handleOpenChange}
      trigger={<Button>Create Folder</Button>}
      title="Create a folder"
      description="Each folder becomes a dedicated VecSeek workspace with its own vector index."
    >
      <form
        className="space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          const cleaned = folderName.trim();
          if (!cleaned) {
            setError("Folder name is required.");
            return;
          }
          mutation.mutate(cleaned);
        }}
      >
        <Input
          placeholder={placeholder}
          value={folderName}
          onChange={(event) => setFolderName(event.target.value)}
        />
        {error ? <p className="text-sm text-danger">{error}</p> : null}
        <div className="flex justify-end">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Creating..." : "Create Folder"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
