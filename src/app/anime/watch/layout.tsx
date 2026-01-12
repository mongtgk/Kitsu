"use client";

import Loading from "@/app/loading";
import parse from "html-react-parser";
import { ROUTES } from "@/constants/routes";

import Container from "@/components/container";
import AnimeCard from "@/components/anime-card";
import { useAnimeStore } from "@/store/anime-store";

import EpisodePlaylist from "@/components/episode-playlist";
import { Heart } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useGetAnimeDetails } from "@/query/get-anime-details";
import React, { ReactNode, useEffect, useMemo, useState } from "react";
import AnimeCarousel from "@/components/anime-carousel";
import { IAnime } from "@/types/anime";
import { toast } from "sonner";
import { useGetAllEpisodes } from "@/query/get-all-episodes";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useAuthSelector } from "@/store/auth-store";

type Props = {
  children: ReactNode;
};

const Layout = (props: Props) => {
  const searchParams = useSearchParams();
  const { setAnime, setSelectedEpisode } = useAnimeStore();
  const router = useRouter();
  const auth = useAuthSelector((state) => state.auth);

  const currentAnimeId = useMemo(
    () => searchParams.get("anime"),
    [searchParams],
  );
  const episodeId = searchParams.get("episode");

  const [animeId, setAnimeId] = useState<string | null>(currentAnimeId);

  useEffect(() => {
    if (currentAnimeId !== animeId) {
      setAnimeId(currentAnimeId);
    }

    if (episodeId) {
      setSelectedEpisode(episodeId);
    }
  }, [currentAnimeId, episodeId, animeId, setSelectedEpisode]);

  const { data: anime, isLoading } = useGetAnimeDetails(animeId as string);

  useEffect(() => {
    if (anime) {
      setAnime(anime);
    }
  }, [anime, setAnime]);

  useEffect(() => {
    if (!animeId) {
      router.push(ROUTES.HOME);
    }
    //eslint-disable-next-line
  }, [animeId, auth]);

  const [isFavorite, setIsFavorite] = useState(false);
  const [favoriteId, setFavoriteId] = useState<string | null>(null);
  const [favoriteLoading, setFavoriteLoading] = useState(false);

  useEffect(() => {
    const loadFavorites = async () => {
      if (!animeId || !api) return;
      if (!auth) {
        setIsFavorite(false);
        return;
      }
      try {
        const res = await api.get("/favorites");
        const match = (res.data as any[])?.find(
          (fav) => fav.anime_id === animeId,
        );
        setIsFavorite(!!match);
        setFavoriteId(match?.id ?? null);
      } catch {
        setIsFavorite(false);
        setFavoriteId(null);
      }
    };
    loadFavorites();
  }, [animeId, auth]);

  const toggleFavorite = async () => {
    if (!animeId) return;
    if (!auth) {
      toast.error("Please login to manage favorites", {
        style: { background: "red" },
      });
      return;
    }
    setFavoriteLoading(true);
    try {
      if (isFavorite) {
        if (!favoriteId) {
          toast.error("Favorite not found to remove", {
            style: { background: "red" },
          });
          return;
        }
        await api.delete(`/favorites/${favoriteId}`);
        setIsFavorite(false);
        setFavoriteId(null);
        toast.success("Removed from favorites", {
          style: { background: "green" },
        });
      } else {
        const res = await api.post("/favorites", { anime_id: animeId });
        setIsFavorite(true);
        setFavoriteId((res.data as any)?.id ?? null);
        toast.success("Added to favorites", { style: { background: "green" } });
      }
    } catch {
      toast.error("Unable to update favorites", {
        style: { background: "red" },
      });
    } finally {
      setFavoriteLoading(false);
    }
  };

  const { data: episodes, isLoading: episodeLoading } = useGetAllEpisodes(
    animeId as string,
  );

  if (isLoading) return <Loading />;

  return (
    anime?.anime.info && (
      <Container className="mt-[6.5rem] space-y-10 pb-20">
        <div className="grid lg:grid-cols-4 grid-cols-1 gap-y-5 gap-x-10 h-auto w-full">
          <div className="lg:col-span-3 col-span-1 lg:mb-0">
            {props.children}
          </div>
          {episodes && (
            <EpisodePlaylist
              animeId={animeId as string}
              title={
                !!anime?.anime.info.name
                  ? anime.anime.info.name
                  : (anime?.anime.moreInfo.japanese as string)
              }
              subOrDub={anime?.anime.info.stats.episodes}
              episodes={episodes}
              isLoading={episodeLoading}
            />
          )}
        </div>
        <div className="flex md:flex-row flex-col gap-5 -mt-5">
          <AnimeCard
            title={anime?.anime.info.name}
            poster={anime?.anime.info.poster}
            subTitle={anime?.anime.moreInfo.aired}
            displayDetails={false}
            className="!h-full !rounded-sm"
            href={ROUTES.ANIME_DETAILS + "/" + anime?.anime.info.id}
          />
          <div className="flex flex-col gap-2">
            <Button
              variant={isFavorite ? "secondary" : "default"}
              className="flex items-center gap-2"
              onClick={toggleFavorite}
              disabled={favoriteLoading}
            >
              <Heart
                className="h-4 w-4"
                fill={isFavorite ? "currentColor" : "none"}
              />
              {isFavorite ? "Remove from Favorites" : "Add to Favorites"}
            </Button>
            <h1 className="text-2xl md:font-black font-extrabold z-[100]">
              {anime?.anime.info.name}
            </h1>
            <p>{parse(anime?.anime.info.description as string)}</p>
          </div>
        </div>
        <AnimeCarousel
          title={"Also Watch"}
          anime={anime?.relatedAnimes as IAnime[]}
        />
        <AnimeCarousel
          title={"Recommended"}
          anime={anime?.recommendedAnimes as IAnime[]}
        />
      </Container>
    )
  );
};
export default Layout;
