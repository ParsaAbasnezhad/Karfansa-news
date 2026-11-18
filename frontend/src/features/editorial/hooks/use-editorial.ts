import { keepPreviousData, useQuery } from "@tanstack/react-query";
import {
  fetchEditorialCategories,
  fetchEditorialDetail,
  fetchEditorialFeatured,
  fetchEditorialLatest,
  fetchEditorialList,
} from "../api/editorial";
import type { EditorialListParams } from "../types/editorial";

export function useEditorialFeatured() {
  return useQuery({
    queryKey: ["editorial", "featured"],
    queryFn: ({ signal }) => fetchEditorialFeatured(signal),
  });
}

export function useEditorialLatest() {
  return useQuery({
    queryKey: ["editorial", "latest"],
    queryFn: ({ signal }) => fetchEditorialLatest(signal),
  });
}

export function useEditorialCategories() {
  return useQuery({
    queryKey: ["editorial", "categories"],
    queryFn: ({ signal }) => fetchEditorialCategories(signal),
  });
}

export function useEditorialList(params: EditorialListParams) {
  return useQuery({
    queryKey: ["editorial", "list", params],
    queryFn: ({ signal }) => fetchEditorialList(params, signal),
    placeholderData: keepPreviousData,
  });
}

export function useEditorialDetail(slug: string) {
  return useQuery({
    queryKey: ["editorial", "detail", slug],
    queryFn: ({ signal }) => fetchEditorialDetail(slug, signal),
    enabled: Boolean(slug),
  });
}
