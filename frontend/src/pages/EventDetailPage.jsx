import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/endpoints';
import EventDetailPanel from '../components/events/EventDetailPanel';
import ErrorState from '../components/ui/ErrorState';
import LoadingState from '../components/ui/LoadingState';

export default function EventDetailPage() {
  const { id } = useParams();
  const [state, setState] = useState({ loading: true, error: null, event: null, analysis: null });

  const load = async () => {
    try {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      const [event, analysis] = await Promise.all([api.getEvent(id), api.getEventAnalysis(id)]);
      setState({ loading: false, error: null, event, analysis });
    } catch (error) {
      setState((prev) => ({ ...prev, loading: false, error }));
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  if (state.loading) return <LoadingState label="Loading event detail…" />;
  if (state.error) return <ErrorState error={state.error} onRetry={load} />;
  return <EventDetailPanel event={state.event} analysis={state.analysis} />;
}
